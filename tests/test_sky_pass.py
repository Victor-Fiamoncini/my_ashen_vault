"""The sky's GPU side without a window: meshes are baked once per lighting and released on change."""

from ashen_vault.render.sky import SkyPass
from ashen_vault.world import sky


class _Gpu:
    def __init__(self):
        self.uploaded = []
        self.unloaded = []

    def upload_batch(self, batch):
        self.uploaded.append(batch)
        return batch

    def unload_mesh(self, mesh):
        self.unloaded.append(mesh)


FOG = (0.42, 0.46, 0.55)


def test_the_sky_is_baked_once_and_rebaked_only_when_the_light_changes():
    gpu = _Gpu()
    sky_pass = SkyPass(gpu)
    spec = sky.SKIES["overcast"]
    sky_pass._bake(spec, FOG, 0.0, False)
    layers = len(sky.layers(spec, FOG))
    assert len(gpu.uploaded) == layers
    textures = [tex for _, tex, _ in sky_pass._meshes]
    # overcast has: dome, stars, cap, far_moon, far_wisps, clouds, sun, mist and the downs (ranges)
    assert textures == [
        "white",
        "white",
        "cloud_cap",
        "white",
        "cloud_cap",
        "clouds",
        "white",
        "mist",
        "white",
    ]
    assert [drifts for _, _, drifts in sky_pass._meshes] == [
        False,
        False,
        True,
        False,
        False,
        True,
        False,
        False,
        False,
    ]
    sky_pass._bake(spec, FOG, 0.001, False)  # a change too small to see reuses the meshes
    assert len(gpu.uploaded) == layers and not gpu.unloaded
    sky_pass._bake(spec, FOG, 0.5, False)  # stepping into the dark rebakes it
    assert len(gpu.uploaded) == layers * 2 and len(gpu.unloaded) == layers
    sky_pass._bake(spec, FOG, 0.5, True)  # so does the Veil
    assert len(gpu.uploaded) == layers * 3


def test_releasing_the_sky_unloads_its_meshes():
    gpu = _Gpu()
    sky_pass = SkyPass(gpu)
    sky_pass._bake(sky.SKIES["ember"], FOG, 0.0, False)
    sky_pass.release()
    assert len(gpu.unloaded) == len(gpu.uploaded) and sky_pass._meshes == []
    sky_pass._bake(sky.SKIES["ember"], FOG, 0.0, False)  # the next frame bakes it afresh
    assert len(gpu.uploaded) == 2 * len(gpu.unloaded)


def test_the_far_moon_is_baked_still_behind_the_drifting_banks():
    gpu = _Gpu()
    sky_pass = SkyPass(gpu)
    sky_pass._bake(sky.SKIES["dusk"], FOG, 0.0, False)
    names = [name for name, _ in sky.layers(sky.SKIES["dusk"], FOG)]
    baked = dict(zip(names, sky_pass._meshes, strict=True))
    assert baked["far_moon"][1:] == ("white", False) and baked["far_wisps"][1:] == ("cloud_cap", False)
    assert baked["clouds"][2] and names.index("far_wisps") < names.index("clouds")
