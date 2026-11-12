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

    def levelup(t, p):
        f = (523.25, 659.25, 783.99, 1046.5)[min(math.floor(p * 4), 3)]
        return math.sin(t * TAU * f) * 0.3 * (1 - p)

    out = {
        "swing": gen(0.22, lambda t, p: lowpass(0.05 + p * 0.25) * env(p, 0.3) * 1.6),
        "hit": gen(
            0.18, lambda t, p: (math.sin(t * TAU * (140 - p * 80)) * 0.8 + noise() * 0.4) * env(p, 0.01)
        ),
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

    def play(self, name, volume=1.0):
        s = self.sounds.get(name) if self.ready else None
        if s is None:
            return
        rl.SetSoundVolume(s, volume)
        rl.PlaySound(s)

    def close(self):
        if self.ready:
            rl.CloseAudioDevice()
