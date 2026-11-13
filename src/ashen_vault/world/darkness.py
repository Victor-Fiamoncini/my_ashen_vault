"""How dark places change what you see: your own light and the fog close in, Lumen pushes them back,
and a Veil of Mist turns the fog pale. Pure math; the game feeds the results to the shader."""

DARK_RADIUS = 3.0  # metres your own light reaches in a pitch-dark place
DARK_GLOW = (0.32, 0.28, 0.22)  # that light's colour where the map gives you none
LUMEN_RADIUS = 9.0  # metres Lumen adds to your light
LUMEN_RGB = (0.6, 0.65, 0.75)
DARK_FOG_RANGE = (2.0, 20.0)  # fog start and end in a pitch-dark place
LUMEN_FOG_RANGE = (5.0, 28.0)  # ...and with Lumen burning
VEIL_FOG = (0.55, 0.58, 0.6)
VEIL_FOG_RANGE = (0.5, 12.0)
VEIL_MIX = 0.7  # how far the veil turns the fog toward its pale grey
EASE_RATE = 1.7  # per second: how fast the eye adjusts to a change in darkness


def _lerp(a, b, k):
    return a + (b - a) * k


def ease_toward(current, target, dt, rate=EASE_RATE):
    """Moves `current` toward `target` by at most `rate * dt`."""
    step = rate * dt
    if abs(target - current) <= step:
        return target
    return current + step if target > current else current - step


def player_light(meta_torch, dark, lumen=False):
    """(radius, rgb) of the light you carry. `meta_torch` is the map's `torch` (radius r g b),
    `dark` the darkness (0..1) where you stand."""
    radius, *rgb = [*meta_torch, 0.0, 0.0, 0.0, 0.0][:4]
    radius = max(radius, 0.0)
    if radius > 0:
        dim_radius, dim_rgb = min(radius, DARK_RADIUS), [c * 0.7 for c in rgb]
    else:
        dim_radius, dim_rgb = DARK_RADIUS, list(DARK_GLOW)
    radius = _lerp(radius, dim_radius, dark)
    rgb = [_lerp(a, b, dark) for a, b in zip(rgb, dim_rgb, strict=True)]
    if lumen:
        return radius + LUMEN_RADIUS, list(LUMEN_RGB)
    return radius, rgb


def fog_for(fog_rgb, fog_range, dark, veil=False, lumen=False):
    """(rgb, (start, end)) of the fog: darkness pulls it in and toward black (Lumen holds it further
    off), a veil turns it pale."""
    near, far = fog_range
    rgb = [c * (1.0 - dark) for c in fog_rgb]
    dark_near, dark_far = LUMEN_FOG_RANGE if lumen else DARK_FOG_RANGE
    near = _lerp(near, min(near, dark_near), dark)
    far = _lerp(far, min(far, dark_far), dark)
    if veil:
        rgb = [_lerp(c, v, VEIL_MIX) for c, v in zip(rgb, VEIL_FOG, strict=True)]
        near, far = min(near, VEIL_FOG_RANGE[0]), min(far, VEIL_FOG_RANGE[1])
    return rgb, (near, far)
