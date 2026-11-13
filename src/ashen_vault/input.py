"""Maps keys and mouse buttons to actions; combat and looking are mouse-only.
An optional script ("forward:1.5 attack wait:1") drives the same actions for
headless smoke runs."""

import raylib as rl

from ashen_vault.screen import to_internal

KEYS = {
    "forward": [rl.KEY_W, rl.KEY_UP],
    "back": [rl.KEY_S, rl.KEY_DOWN],
    "strafe_l": [rl.KEY_A],
    "strafe_r": [rl.KEY_D],
    "sprint": [rl.KEY_LEFT_SHIFT, rl.KEY_RIGHT_SHIFT],
    "interact": [rl.KEY_E],
    "menu": [rl.KEY_TAB, rl.KEY_I],
    "pause": [rl.KEY_ESCAPE],
    "up": [rl.KEY_W, rl.KEY_UP],
    "down": [rl.KEY_S, rl.KEY_DOWN],
    "confirm": [rl.KEY_ENTER, rl.KEY_E, rl.KEY_SPACE],
    "cancel": [rl.KEY_ESCAPE, rl.KEY_TAB, rl.KEY_BACKSPACE],
}
MOUSE = {
    "attack": rl.MOUSE_BUTTON_LEFT,
    "cast": rl.MOUSE_BUTTON_RIGHT,
    "click": rl.MOUSE_BUTTON_LEFT,
    "back": rl.MOUSE_BUTTON_RIGHT,
    "quick": rl.MOUSE_BUTTON_MIDDLE,
}
SCRIPT_WHEEL = {"wheel_up": 1, "wheel_down": -1}

# What the Controls screen shows. Keep in sync with KEYS / MOUSE.
CONTROLS = [
    ("Move", "W S / Up Down"),
    ("Strafe", "A D"),
    ("Sprint", "Hold Shift"),
    ("Turn / look", "Mouse"),
    ("Attack", "Left mouse"),
    ("Cast spell", "Right mouse"),
    ("Change spell", "Mouse wheel"),
    ("Quick item", "Middle mouse"),
    ("Choose quick item", "Shift + wheel"),
    ("Use, talk, open", "E"),
    ("Belongings", "Tab / I"),
    ("Pause", "Esc"),
    ("Menus", "Up Down, Enter, Esc"),
    ("Menus (mouse)", "Point, click, right-click"),
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
        self._mouse = None

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

    def wheel(self):
        """Mouse wheel steps this frame: positive = up."""
        if self._pressed in SCRIPT_WHEEL:
            return SCRIPT_WHEEL[self._pressed]
        return rl.GetMouseWheelMove()

    def pointer(self):
        """(x, y, moved) of the mouse in 320x240 space, or None outside the picture.
        `moved` is True only on frames the mouse actually moved, so a resting
        cursor never fights keyboard navigation."""
        pos = rl.GetMousePosition()
        at = (pos.x, pos.y)
        moved = self._mouse is not None and at != self._mouse
        self._mouse = at
        mapped = to_internal(pos.x, pos.y, rl.GetScreenWidth(), rl.GetScreenHeight())
        if mapped is None:
            return None
        return mapped[0], mapped[1], moved
