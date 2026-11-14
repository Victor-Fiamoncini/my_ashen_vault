"""Player options kept apart from the run: sound on or off and its volume. They live in
`settings.json` beside the save file, so a throwaway ASHEN_VAULT_SAVE keeps its own settings."""

import json
import os

from ashen_vault.util import clamp, rround

VOLUME_STEP = 0.1


class Settings:
    def __init__(self, path, sound=True, volume=0.8):
        self.path = path
        self.sound = sound
        self.volume = volume

    @classmethod
    def beside(cls, save_path):
        """The settings stored next to the save at `save_path`, or the defaults if there are none."""
        return cls.load(os.path.join(os.path.dirname(save_path) or ".", "settings.json"))

    @classmethod
    def load(cls, path):
        s = cls(path)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            s.sound = bool(data.get("sound", s.sound))
            s.volume = s._clamped(float(data.get("volume", s.volume)))
        except (OSError, ValueError, TypeError, AttributeError):
            pass
        return s

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"sound": self.sound, "volume": self.volume}, f, indent=2)
        except OSError:
            pass

    @staticmethod
    def _clamped(v):
        return rround(clamp(v, 0.0, 1.0) * 10) / 10  # whole steps of 10%

    @property
    def gain(self):
        """The master volume to play at: silent while sound is off."""
        return self.volume if self.sound else 0.0

    def toggle_sound(self):
        self.sound = not self.sound

    def step_volume(self, steps, wrap=False):
        v = self.volume + steps * VOLUME_STEP
        if wrap and v > 1.0 + 1e-6:
            v = 0.0
        self.volume = self._clamped(v)

    @property
    def percent(self):
        return rround(self.volume * 100)
