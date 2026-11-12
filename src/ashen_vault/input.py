"""Maps keys to actions. An optional script ("forward:1.5 attack wait:1")
drives the same actions for headless smoke runs."""

import raylib as rl

KEYS = {
    "forward": [rl.KEY_W, rl.KEY_UP],
    "back": [rl.KEY_S, rl.KEY_DOWN],
    "strafe_l": [rl.KEY_A],
    "strafe_r": [rl.KEY_D],
    "turn_l": [rl.KEY_LEFT],
    "turn_r": [rl.KEY_RIGHT],
    "look_up": [rl.KEY_PAGE_UP],
    "look_down": [rl.KEY_PAGE_DOWN],
    "sprint": [rl.KEY_LEFT_SHIFT, rl.KEY_RIGHT_SHIFT],
    "attack": [rl.KEY_SPACE],
    "cast": [rl.KEY_F],
    "interact": [rl.KEY_E],
    "cycle": [rl.KEY_R],
    "menu": [rl.KEY_TAB, rl.KEY_I],
    "pause": [rl.KEY_ESCAPE],
    "quick1": [rl.KEY_ONE],
    "quick2": [rl.KEY_TWO],
    "up": [rl.KEY_W, rl.KEY_UP],
    "down": [rl.KEY_S, rl.KEY_DOWN],
    "confirm": [rl.KEY_ENTER, rl.KEY_E, rl.KEY_SPACE],
    "cancel": [rl.KEY_ESCAPE, rl.KEY_TAB, rl.KEY_BACKSPACE],
}
MOUSE = {"attack": rl.MOUSE_BUTTON_LEFT, "cast": rl.MOUSE_BUTTON_RIGHT}

# What the Controls screen shows. Keep in sync with KEYS / MOUSE.
CONTROLS = [
    ("Move", "W S / Up Down"),
    ("Strafe", "A D"),
    ("Sprint", "Hold Shift"),
    ("Turn / look", "Mouse, Left Right"),
    ("Look up / down", "PgUp PgDn"),
    ("Attack", "Space / Left mouse"),
    ("Cast spell", "F / Right mouse"),
    ("Change spell", "R"),
    ("Use, talk, open", "E"),
    ("Belongings", "Tab / I"),
    ("Red Tonic / Blue Moss", "1 / 2"),
    ("Pause", "Esc"),
    ("Menus", "Up Down, Enter, Esc"),
]


class Input:
    def __init__(self, script=None):
        self._steps = []
        for tok in (script or "").split():
            action, _, secs = tok.partition(":")
            self._steps.append((action, float(secs) if secs else None))
        self._held = None
        self._held_t = 0.0
        self._pressed = None
        self._wait = 0.0

    @property
    def scripted(self):
        return bool(self._steps) or self._held is not None or self._wait > 0

    def update(self, dt):
        self._pressed = None
        if self._held is not None:
            self._held_t -= dt
            if self._held_t <= 0:
                self._held = None
            return
        if self._wait > 0:
            self._wait -= dt
            return
        if not self._steps:
            return
        action, secs = self._steps.pop(0)
        if action == "wait":
            self._wait = secs if secs is not None else 1.0
        elif secs is not None:
            self._held = action
            self._held_t = secs
        else:
            self._pressed = action

    def down(self, action):
        if self._held == action:
            return True
        if any(rl.IsKeyDown(k) for k in KEYS.get(action, ())):
            return True
        return action in MOUSE and rl.IsMouseButtonDown(MOUSE[action])

    def pressed(self, action):
        if self._pressed == action:
            return True
        if any(rl.IsKeyPressed(k) for k in KEYS.get(action, ())):
            return True
        return action in MOUSE and rl.IsMouseButtonPressed(MOUSE[action])
