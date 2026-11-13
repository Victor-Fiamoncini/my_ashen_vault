"""Spell bolts in three dimensions: which way they fly and what they strike. Pure, no raylib.

A bolt leaves along the player's view, pitch included, and only hits an enemy whose body it actually
passes through: shoot level over a slime and the bolt sails over it; look down to hit it. Enemy shots
are aimed at your chest the same way, so you can drop below one fired from a ledge."""

import math

BOLT_SPEED = 9.0  # metres per second
BOLT_DROP = 0.25  # metres below the eye the bolt sets out from (it leaves the casting hand)
BOLT_SIZE = 0.15  # half the bolt's height, counted as touching a body it grazes
HOVER_BODY = 0.4  # half the height of a hovering enemy's body, around its hover height
PLAYER_TALL = 1.8  # top of the player's body above their feet
PLAYER_RADIUS = 0.3  # with the 0.3 grace in strikes(), shots within 0.6 m across the ground can hit
AIM_HEIGHT = 1.0  # enemies aim at your chest, this far above your feet


def aim(yaw, pitch, speed=BOLT_SPEED):
    """Velocity (dx, dy, dz) of a bolt fired along the view."""
    cp = math.cos(pitch)
    return math.cos(yaw) * cp * speed, math.sin(pitch) * speed, math.sin(yaw) * cp * speed


def toward(x, y, z, tx, ty, tz, speed, spread=0.0):
    """Velocity (dx, dy, dz) of a shot from (x, y, z) at (tx, ty, tz): `speed` across the ground,
    turned `spread` radians sideways, climbing or dropping to arrive at the target's height."""
    across = math.hypot(tx - x, tz - z)
    yaw = math.atan2(tz - z, tx - x) + spread
    dy = (ty - y) / across * speed if across > 1e-6 else 0.0
    return math.cos(yaw) * speed, dy, math.sin(yaw) * speed


def player_span(feet_y):
    return feet_y, feet_y + PLAYER_TALL


def body_span(type_, floor_y):
    """Lowest and highest point of an enemy's body standing on `floor_y`."""
    if type_.hover is not None:
        return floor_y + type_.hover - HOVER_BODY, floor_y + type_.hover + HOVER_BODY
    return floor_y, floor_y + type_.tall


def strikes(x, y, z, ex, ez, radius, span):
    """Whether a bolt at (x, y, z) touches a body of `radius` at (ex, ez) spanning `span` in height."""
    lo, hi = span
    return math.hypot(x - ex, z - ez) < radius + 0.3 and lo - BOLT_SIZE <= y <= hi + BOLT_SIZE
