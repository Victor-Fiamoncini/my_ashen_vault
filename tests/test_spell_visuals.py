"""Thunder Spear and Arcane Motes as drawn: in flight, in Belongings and over the palm."""

from ashen_vault.render import forge_models, models, rig


class _Parts:
    def __init__(self):
        self.parts = []

    def to_matrix(self, m):
        return m

    def draw_part(self, kind, m, rgb, tex="white", glow=False):
        self.parts.append((kind, tuple(rgb), round(m[3], 4), round(m[7], 4), round(m[11], 4), glow))


def _draw(fn, *args):
    gpu = _Parts()
    fn(rig.Rig(gpu), *args)
    return gpu.parts


def test_a_lightning_bolt_is_struck_anew_each_flicker_but_holds_between():
    step = 1 / forge_models.BOLT_FLICKER
    a = forge_models.bolt_points(0.01)
    assert forge_models.bolt_points(0.01 + step * 0.5) == a  # within one flicker it holds still
    b = forge_models.bolt_points(0.01 + step)
    assert a != b
    assert a[0] == b[0] and a[-1] == b[-1]  # its ends stay put: it always runs tail to point
    xs = [x for x, _, _ in a]
    assert xs == sorted(xs)


def test_the_thunder_spear_and_a_mote_glow_and_change_as_they_fly():
    for fn in (forge_models.thunder_spear, forge_models.mote):
        now, later = _draw(fn, 0.0), _draw(fn, 0.13)
        assert now != later, fn.__name__
        assert all(glow for *_, glow in now), fn.__name__  # all light, nothing dark to cast a shadow
    tail = [x for _, _, x, *_ in _draw(forge_models.mote, 0.0)]
    assert min(tail) < -0.4  # its comet tail streams out behind it


def test_thunder_and_motes_have_their_own_previews_not_the_plain_orb():
    plain = len(_draw(models.spell_orb, "venom", 0.0))
    for id_ in ("thunder", "motes", "mend", "lumen"):
        parts = _draw(models.spell_orb, id_, 0.4)
        assert len(parts) > plain * 2, id_
        assert parts != _draw(models.spell_orb, id_, 0.9), id_  # it moves


def test_mend_and_lumen_look_unlike_each_other_and_glow():
    mend, lumen = _draw(models.spell_orb, "mend", 0.4), _draw(models.spell_orb, "lumen", 0.4)
    assert all(glow for *_, glow in mend + lumen)  # all light
    assert {rgb for _, rgb, *_ in mend}.isdisjoint({rgb for _, rgb, *_ in lumen})
    rays = [p for p in lumen if p[0] == "cube" and p[1] == models.LUMEN_CORE]
    assert len(rays) == models.LUMEN_RAYS


def test_mend_and_lumen_have_their_own_light_over_the_palm():
    def palm(fn, t, ready, cast):
        gpu = _Parts()
        fn(rig.Rig(gpu), t, ready, cast)
        return gpu.parts

    for fn in (models._palm_mend, models._palm_lumen):
        ready = palm(fn, 0.3, True, 0.0)
        assert len(ready) >= 5, fn.__name__
        assert ready != palm(fn, 0.8, True, 0.0), fn.__name__  # it moves
        assert len(palm(fn, 0.3, False, 0.8)) > len(palm(fn, 0.3, False, 0.0)), fn.__name__  # a cast shows
