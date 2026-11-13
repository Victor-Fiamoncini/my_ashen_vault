import math


def rround(x):
    """Round half away from zero, like Ruby's Float#round (Python rounds half to even)."""
    return int(math.copysign(math.floor(abs(x) + 0.5), x))


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def highlight_runs(text):
    """Splits message markup into [(segment, highlighted)]: `{...}` marks a highlighted span
    (an item name, a sum of gold). An unclosed brace is kept as plain text."""
    runs = []
    rest = text
    while rest:
        start = rest.find("{")
        end = rest.find("}", start + 1) if start >= 0 else -1
        if start < 0 or end < 0:
            runs.append((rest, False))
            break
        if start:
            runs.append((rest[:start], False))
        if end > start + 1:
            runs.append((rest[start + 1 : end], True))
        rest = rest[end + 1 :]
    return runs


def plain(text):
    """`text` with the highlight braces stripped."""
    return "".join(seg for seg, _ in highlight_runs(text))
