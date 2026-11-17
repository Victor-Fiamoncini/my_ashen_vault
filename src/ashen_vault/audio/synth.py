"""Generates every sound effect at startup as 16-bit mono WAV data."""

import math
import random
import struct
import sys
from array import array

import raylib as rl
from raylib import ffi

from ashen_vault.util import rround

RATE = 22_050
BONE_CRUNCH = 0.12  # seconds the splintering crackle of a blow on bone lasts
TAU = 2 * math.pi


def wav(samples):
    pcm = array("h", (rround(max(-1.0, min(1.0, s)) * 32_000) for s in samples))
    if sys.byteorder == "big":
        pcm.byteswap()
    data = pcm.tobytes()
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + len(data),
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        RATE,
        RATE * 2,
        2,
        16,
        b"data",
        len(data),
    )
    return header + data


def gen(seconds, fn):
    n = rround(seconds * RATE)
    return [fn(i / RATE, i / n) for i in range(n)]


def env(p, attack=0.02):
    return p / attack if p < attack else (1 - p) ** 2


def noise():
    return random.random() * 2 - 1


def sounds():
    lp = [0.0]  # shared low-pass state, carried across sounds like the original

    def lowpass(k):
        lp[0] += (noise() - lp[0]) * k
        return lp[0]

    whoosh, roar, crack = [0.0], [0.0], [0.0]

    def pyre(t, p):
        # The whoosh opens bright then darkens; the roar is filtered noise beating against a low hum.
        cut = 0.08 + 0.55 * min(p / 0.12, 1.0) * (1 - p) ** 1.5
        whoosh[0] += (noise() - whoosh[0]) * cut
        roar[0] += (noise() - roar[0]) * 0.03
        hum = math.sin(t * TAU * (62 + 20 * (1 - p))) * 0.35
        if random.random() < 0.004 * (1 - p * 0.6):  # sparse pops and crackles
            crack[0] = noise()
        crack[0] *= 0.82
        body = whoosh[0] * 1.6 * env(p, 0.04) + (roar[0] * 3.2 + hum) * env(p, 0.12) * 0.7
        return body + crack[0] * 0.55 * (1 - p)

    swell, pop = [0.0], [0.0]

    def rise(t, p):
        # A boss rising from its ashes: a fire roar swelling up from nothing over a low drone that
        # climbs in pitch, embers crackling ever faster, cut off as it stands whole.
        swell[0] += (noise() - swell[0]) * (0.02 + 0.2 * p)
        drone = math.sin(t * TAU * (40 + 50 * p)) * 0.4 + math.sin(t * TAU * (60 + 75 * p)) * 0.2
        if random.random() < 0.001 + 0.008 * p:
            pop[0] = noise()
        pop[0] *= 0.8
        level = p**1.4 * min((1 - p) / 0.08, 1.0)
        return (swell[0] * 2.6 + drone) * level + pop[0] * 0.5 * p

    # Blows landing on a foe, one per material (EnemyType.material). Each opens on a short sharp click,
    # the moment of contact, under a body of its own.
    def click(t):
        return noise() * math.exp(-t * 900) * 0.9

    def thump(t, top, bottom, fall, decay):
        return math.sin(t * TAU * (bottom + (top - bottom) * math.exp(-t * fall))) * math.exp(-t * decay)

    wet, grit = [0.0], [0.0]

    def hit_flesh(t, p):
        # A low wet thump, the swing biting into meat.
        wet[0] += (noise() - wet[0]) * 0.12
        return click(t) * 0.6 + thump(t, 110, 45, 30, 16) * 0.9 + wet[0] * 1.8 * math.exp(-t * 22)

    lo, hi = [0.0], [0.0]

    def hit_bone(t, p):
        # Bone giving way: a dull, heavy knock and, over it, a dry crunch of splinters, sparse grains of
        # noise in a narrow band (no pitched tones, which turn it into a xylophone).
        grain = noise() if random.random() < 0.35 * math.exp(-t * 18) else noise() * 0.12
        lo[0] += (grain - lo[0]) * 0.45  # low-pass, then take the lows back off: a band round 2 kHz
        hi[0] += (lo[0] - hi[0]) * 0.08
        crunch = (lo[0] - hi[0]) * 2.0 * max(0.0, 1 - t / BONE_CRUNCH)
        return click(t) * 0.7 + thump(t, 95, 55, 40, 24) * 0.75 + crunch

    def hit_iron(t, p):
        # A clang: inharmonic partials ringing out over the thump of the blow.
        ring = (
            (
                math.sin(t * TAU * 523) * 0.35
                + math.sin(t * TAU * 1381) * 0.22
                + math.sin(t * TAU * 2097) * 0.14
            )
            * math.exp(-t * 9)
            * (1 + 0.3 * math.sin(t * TAU * 7))
        )
        return click(t) + ring + thump(t, 140, 70, 30, 25) * 0.5

    def hit_stone(t, p):
        # A dull knock and grit spraying off the stone.
        grit[0] = noise() if random.random() < 0.06 else grit[0] * 0.7
        return click(t) * 0.8 + thump(t, 160, 55, 45, 22) * 0.9 + grit[0] * 0.5 * math.exp(-t * 14)

    def hit_wood(t, p):
        # A hollow knock with a few partials and a splintery tail.
        knock = (math.sin(t * TAU * 220) + math.sin(t * TAU * 487) * 0.5 + math.sin(t * TAU * 761) * 0.25) * (
            math.exp(-t * 28)
        )
        splinter = noise() * math.exp(-t * 30) * (1.0 if random.random() < 0.3 else 0.2)
        return click(t) * 0.8 + knock * 0.5 + splinter * 0.4

    def hit_ash(t, p):
        # A soft, muffled thump and ash crumbling away in a hiss.
        wet[0] += (noise() - wet[0]) * 0.3
        return click(t) * 0.3 + thump(t, 90, 50, 25, 18) * 0.7 + wet[0] * 0.9 * env(p, 0.15) * (1 - p)

    def levelup(t, p):
        f = (523.25, 659.25, 783.99, 1046.5)[min(math.floor(p * 4), 3)]
        return math.sin(t * TAU * f) * 0.3 * (1 - p)

    out = {
        "swing": gen(0.22, lambda t, p: lowpass(0.05 + p * 0.25) * env(p, 0.3) * 1.6),
        "hit": gen(
            0.18, lambda t, p: (math.sin(t * TAU * (140 - p * 80)) * 0.8 + noise() * 0.4) * env(p, 0.01)
        ),
        "hit_flesh": gen(0.25, hit_flesh),
        "hit_bone": gen(0.22, hit_bone),
        "hit_iron": gen(0.5, hit_iron),
        "hit_stone": gen(0.3, hit_stone),
        "hit_wood": gen(0.25, hit_wood),
        "hit_ash": gen(0.35, hit_ash),
        "hurt": gen(
            0.3, lambda t, p: (math.sin(t * TAU * (220 - p * 120)) + noise() * 0.3) * 0.6 * env(p, 0.01)
        ),
        "door": gen(0.9, lambda t, p: (lowpass(0.02) * 3 + math.sin(t * TAU * 55) * 0.3) * env(p, 0.1)),
        "chest": gen(
            0.35,
            lambda t, p: math.sin(t * TAU * (300 + p * 200)) * 0.25 * env(p, 0.05) + noise() * 0.1 * (1 - p),
        ),
        "pickup": gen(
            0.4, lambda t, p: (math.sin(t * TAU * (660 if p < 0.5 else 880)) * 0.35) * env(p, 0.02)
        ),
        "spell": gen(
            0.5,
            lambda t, p: (
                (lowpass(0.15) * 0.8 + math.sin(t * TAU * (400 + math.sin(t * 40) * 60)) * 0.2) * env(p, 0.15)
            ),
        ),
        "enemy_die": gen(
            0.7,
            lambda t, p: (math.sin(t * TAU * (180 - p * 140)) * 0.5 + noise() * 0.3 * (1 - p)) * env(p, 0.01),
        ),
        "levelup": gen(0.9, levelup),
        "trap": gen(
            0.35,
            lambda t, p: (
                (noise() * 0.5 * (1 - p) + math.sin(t * TAU * (900 - p * 600)) * 0.25) * env(p, 0.01)
                + math.sin(t * TAU * 70) * 0.4 * env(p, 0.02)
            ),
        ),
        "crack": gen(
            0.4,
            lambda t, p: (
                (noise() * (1.0 if (t * 37) % 1 < 0.3 else 0.2) + math.sin(t * TAU * (160 - p * 90)) * 0.3)
                * env(p, 0.01)
            ),
        ),
        "swoosh": gen(0.45, lambda t, p: lowpass(0.04 + math.sin(p * math.pi) * 0.25) * 2.0 * env(p, 0.45)),
        "save": gen(
            1.2, lambda t, p: (math.sin(t * TAU * 392) + math.sin(t * TAU * 588)) * 0.18 * env(p, 0.2)
        ),
        "bell": gen(
            3.0,
            lambda t, p: (
                sum(math.sin(t * TAU * 196 * h) / h for h in (1.0, 2.4, 3.0, 4.5)) * 0.25 * (1 - p) ** 3
            ),
        ),
        "step": gen(0.08, lambda t, p: lowpass(0.3) * 0.5 * env(p, 0.05)),
        # Footsteps, one per surface underfoot (`world/footsteps.py`).
        # Stone: a short, bright scuff of grit and a hard heel.
        "step_stone": gen(
            0.07, lambda t, p: (lowpass(0.55) * 0.45 + math.sin(t * TAU * 180) * 0.15) * env(p, 0.04)
        ),
        # Wood: a hollow knock that rings low in the boards.
        "step_wood": gen(
            0.13,
            lambda t, p: (
                (math.sin(t * TAU * 130) * 0.5 + math.sin(t * TAU * 210) * 0.2) * (1 - p) ** 3
                + lowpass(0.35) * 0.25 * env(p, 0.03)
            ),
        ),
        # Soft earth, ash and leaves: a dull, muffled pad.
        "step_soft": gen(0.1, lambda t, p: lowpass(0.08) * 1.4 * env(p, 0.15)),
        # Mud: a wet squelch, its low-pass closing as the foot sinks in.
        "step_mud": gen(
            0.2,
            lambda t, p: (
                (lowpass(0.04 + 0.2 * (1 - p)) * 1.6 + math.sin(t * TAU * (95 - p * 45)) * 0.2) * env(p, 0.2)
            ),
        ),
        # Shallow water: a little slosh and spray.
        "step_water": gen(
            0.22, lambda t, p: (lowpass(0.4 - p * 0.3) * 1.0 + lowpass(0.05) * 0.6) * env(p, 0.1)
        ),
        # Iron plate and grates: a tap with a faint ring.
        "step_metal": gen(
            0.18,
            lambda t, p: (
                (
                    lowpass(0.5) * 0.3 * (1 - p) ** 6
                    + (math.sin(t * TAU * 620) * 0.18 + math.sin(t * TAU * 1430) * 0.08) * (1 - p) ** 3
                )
                * env(p, 0.01)
            ),
        ),
        # Slag and loose scree: a crunch of a few gritty bursts.
        "step_gravel": gen(
            0.12,
            lambda t, p: noise() * 0.5 * env(p, 0.05) * (0.35 + 0.65 * (math.sin(t * TAU * 55) > 0.2)),
        ),
        "heavy": gen(
            0.4,
            lambda t, p: (
                (lowpass(0.03 + p * 0.12) * 2.2 + math.sin(t * TAU * (90 - p * 40)) * 0.3) * env(p, 0.4)
            ),
        ),
        # Something heavy dropping into water: a thump, then a hiss of spray that falls away.
        "splash": gen(
            0.6,
            lambda t, p: (
                (lowpass(0.25 - p * 0.2) * 1.8 * (1 - p) ** 2 + math.sin(t * TAU * (110 - p * 70)) * 0.35)
                * env(p, 0.01)
            ),
        ),
        # Two low, buzzing croaks from a stone frog.
        "croak": gen(
            0.55,
            lambda t, p: (
                math.sin(t * TAU * (95 + 30 * math.sin(t * TAU * 22)))
                * (0.6 if (p < 0.4 or 0.55 < p < 0.95) else 0.0)
                * env(p, 0.02)
            ),
        ),
        # A slam: a deep thud with a rumble of stone after it.
        "quake": gen(
            0.8,
            lambda t, p: (
                (math.sin(t * TAU * (60 - p * 30)) * 0.8 + lowpass(0.04) * 2.0 * (1 - p)) * env(p, 0.01)
            ),
        ),
        # Fire roaring up from the floor.
        "eruption": gen(
            0.9, lambda t, p: (lowpass(0.2 + p * 0.1) * 1.6 + noise() * 0.2) * math.sin(p * math.pi) ** 0.5
        ),
        # A chain paying out over a winch: quick metallic ticks.
        "chain": gen(
            0.7,
            lambda t, p: (
                (math.sin(t * TAU * 1400) * 0.25 + noise() * 0.35)
                * (1.0 if (t * 18) % 1 < 0.25 else 0.1)
                * env(p, 0.05)
            ),
        ),
        # A heavy platform settling into place.
        "clunk": gen(
            0.35,
            lambda t, p: (math.sin(t * TAU * (95 - p * 40)) * 0.7 + lowpass(0.1) * 0.8) * env(p, 0.01),
        ),
        # A soft cough of spores from a bursting pod.
        "puff": gen(0.5, lambda t, p: lowpass(0.08 + (1 - p) * 0.1) * 1.6 * env(p, 0.15)),
        # Pyre: a rushing whoosh as the gout leaves your hand, a low roar under it and fire crackling.
        "pyre": gen(0.75, pyre),
        # A brazier or bonfire catching.
        "kindle": gen(
            0.55, lambda t, p: (lowpass(0.25 + (1 - p) * 0.2) * 2.0 + noise() * 0.25) * env(p, 0.08)
        ),
        # Venom sizzling, or mist breathed out (Veil of Mist).
        "hiss": gen(0.6, lambda t, p: noise() * 0.5 * math.sin(p * math.pi) * (0.6 + 0.4 * math.sin(t * 60))),
        # A crack of thunder: a sharp snap, then a rolling rumble (Thunder Spear).
        "thunder": gen(
            0.9,
            lambda t, p: (
                noise() * 0.9 * max(1 - p * 8, 0.0)
                + (lowpass(0.05) * 2.2 + math.sin(t * TAU * (55 + 20 * math.sin(t * 9))) * 0.3)
                * (1 - p) ** 1.5
            ),
        ),
        # A hammer ringing on the anvil: a bright clink over a short, falling metallic ring (the smith).
        "anvil": gen(
            0.45,
            lambda t, p: (
                noise() * 0.5 * max(1 - p * 25, 0.0)
                + (
                    math.sin(t * TAU * 1870) * 0.35
                    + math.sin(t * TAU * 2650) * 0.2
                    + math.sin(t * TAU * 940) * 0.2
                )
                * (1 - p) ** 3
            ),
        ),
        # Three glassy chimes, rising (Arcane Motes).
        "motes": gen(
            0.6,
            lambda t, p: (
                math.sin(t * TAU * (880, 1175, 1568)[min(math.floor(p * 3), 2)])
                * math.sin(t * TAU * 6) ** 2
                * 0.3
                * (1 - p)
            ),
        ),
        # An Ashen Ward kindling: a low ember swell that rises and settles, a soft chime as it closes.
        "ward": gen(
            0.9,
            lambda t, p: (
                (math.sin(t * TAU * (98 + 40 * p)) * 0.35 + lowpass(0.05) * 1.4) * math.sin(p * math.pi)
                + math.sin(t * TAU * 660) * 0.2 * max(1 - abs(p - 0.4) * 5, 0.0)
                + math.sin(t * TAU * 990) * 0.1 * max(1 - abs(p - 0.45) * 5, 0.0)
            ),
        ),
        # A flame jet roaring out of its nozzle.
        "jet": gen(
            1.0, lambda t, p: (lowpass(0.35) * 1.8 + noise() * 0.3) * min(p / 0.08, 1.0) * (1 - p) ** 0.6
        ),
        # A magma vent coughing up a bomb: a deep gulp and a whoosh.
        "lob": gen(
            0.6, lambda t, p: (math.sin(t * TAU * (70 + p * 60)) * 0.6 + lowpass(0.1) * 1.2) * env(p, 0.05)
        ),
        # A gargoyle's breath: a long roar that swells and fades.
        "breath": gen(1.2, lambda t, p: (lowpass(0.18) * 2.2 + noise() * 0.2) * math.sin(p * math.pi) ** 0.7),
        # A boss forming out of the burning ash of its heap.
        "rise": gen(2.6, rise),
        # Iron grinding on stone, then a metallic shriek (the gargoyles waking).
        "screech": gen(
            1.1,
            lambda t, p: (
                (math.sin(t * TAU * (700 + 500 * p + 80 * math.sin(t * 50))) * 0.3 + noise() * 0.25 * (1 - p))
                * env(p, 0.2)
            ),
        ),
    }
    return {name: wav(s) for name, s in out.items()}


class Audio:
    """Plays synthesized sounds through raylib; silently does nothing without an audio device."""

    def __init__(self):
        rl.InitAudioDevice()
        self.ready = rl.IsAudioDeviceReady()
        self.sounds = {}
        if not self.ready:
            return
        for name, data in sounds().items():
            buf = ffi.new("unsigned char[]", data)
            wave = rl.LoadWaveFromMemory(b".wav", buf, len(data))
            self.sounds[name] = rl.LoadSoundFromWave(wave)
            rl.UnloadWave(wave)

    def play(self, name, volume=1.0, pitch=1.0):
        s = self.sounds.get(name) if self.ready else None
        if s is None:
            return
        rl.SetSoundVolume(s, volume)
        rl.SetSoundPitch(s, pitch)
        rl.PlaySound(s)

    def set_volume(self, v):
        """Master gain for every sound (0 silences them all)."""
        if self.ready:
            rl.SetMasterVolume(v)

    def close(self):
        if self.ready:
            rl.CloseAudioDevice()
