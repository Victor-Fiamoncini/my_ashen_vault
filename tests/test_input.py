from ashen_vault.input import CONTROLS, KEYS, MOUSE

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
