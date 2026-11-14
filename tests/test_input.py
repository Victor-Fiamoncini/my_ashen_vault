from ashen_vault.input import CONTROLS, KEYS, MOUSE, PointerTracker

MOVEMENT = ("forward", "back", "strafe_l", "strafe_r", "sprint")


def test_mouse_buttons_never_drive_movement():
    """Holding a mouse button (a raised shield) must never read as a step: an action named in
    MOUSE may not also be a movement key."""
    assert not set(MOUSE) & set(MOVEMENT)


def test_mouse_and_key_actions_do_not_share_names_by_accident():
    shared = set(MOUSE) & set(KEYS)
    assert shared == set(), shared


def test_controls_name_slots_not_hands():
    labels = [k for k, _ in CONTROLS]
    assert "Primary" in labels and "Secondary" in labels
    assert not any("hand" in k.lower() for k in labels)


def test_pointer_motion_is_the_same_for_every_caller_in_a_frame():
    """The Belongings tabs read the pointer before its rows; the rows must still see the move."""
    t = PointerTracker()
    t.next_frame()
    assert not t.moved((10, 10))  # first sighting
    t.next_frame()
    assert t.moved((12, 10)) and t.moved((12, 10))
    t.next_frame()
    assert not t.moved((12, 10))
