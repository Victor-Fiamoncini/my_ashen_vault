import math

import pytest

from ashen_vault.world import atlas


def test_the_volcano_stands_where_the_cinderhold_first_saw_it():
    s = atlas.sight("cinderhold", "volcano")
    assert s.azimuth == pytest.approx(atlas.VOLCANO_BEARING)
    assert s.km == pytest.approx(atlas.VOLCANO_KM)


def test_the_lands_lie_round_harrowmere():
    def bearing(a, b):
        ax, az, _ = atlas.PLACES[a]
        bx, bz, _ = atlas.PLACES[b]
        return math.degrees(math.atan2(bz - az, bx - ax)) % 360

    assert 170 < bearing("harrowmere", "ashen_cemetery") < 190  # west
    assert bearing("harrowmere", "verdant_hollow") < 20  # east
    assert 240 < bearing("harrowmere", "cinderhold") < 270  # north-north-west, up the north road
    assert 270 < bearing("harrowmere", "vesperholm") < 300  # north-north-east, through the Vesper Gate
    assert atlas.PLACES["cinder_keep"] == atlas.PLACES["cinderhold"]


def test_a_place_does_not_see_the_landmark_it_stands_on():
    assert atlas.sight("herrans_castle", "hollow_peak") is None
    assert atlas.sight("vesperholm", "hollow_peak") is not None


def test_higher_eyes_see_landmarks_lower_and_nearer_ones_taller():
    far = atlas.sight("harrowmere", "volcano")
    near = atlas.sight("cinderhold", "volcano")
    assert near.elevation > far.elevation
    assert (
        0
        < atlas.sight("herrans_castle", "volcano").elevation
        < atlas.sight("vesperholm", "volcano").elevation
    )


def test_place_reads_the_maps_meta():
    assert atlas.place({"atlas": " harrowmere "}) == "harrowmere"
    assert atlas.place({"atlas": "nowhere"}) is None
    assert atlas.place({}) is None
