import math


def rround(x):
    """Round half away from zero, like Ruby's Float#round (Python rounds half to even)."""
    return int(math.copysign(math.floor(abs(x) + 0.5), x))


def clamp(v, lo, hi):
    return max(lo, min(hi, v))
