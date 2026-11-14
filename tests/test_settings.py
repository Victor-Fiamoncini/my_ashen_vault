from ashen_vault.save.settings import Settings


def test_defaults_when_there_is_no_file(tmp_path):
    s = Settings.beside(str(tmp_path / "save.json"))
    assert s.path == str(tmp_path / "settings.json")
    assert (s.sound, s.volume, s.percent, s.gain) == (True, 0.8, 80, 0.8)


def test_settings_round_trip_beside_the_save(tmp_path):
    s = Settings.beside(str(tmp_path / "save.json"))
    s.toggle_sound()
    s.step_volume(-3)
    s.save()
    back = Settings.beside(str(tmp_path / "save.json"))
    assert (back.sound, back.volume, back.gain) == (False, 0.5, 0.0)


def test_volume_steps_clamp_and_wrap(tmp_path):
    s = Settings(str(tmp_path / "settings.json"), volume=0.9)
    s.step_volume(1)
    s.step_volume(1)
    assert s.volume == 1.0
    s.step_volume(1, wrap=True)
    assert s.volume == 0.0
    s.step_volume(-1)
    assert s.volume == 0.0


def test_a_corrupt_file_falls_back_to_the_defaults(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text("{not json")
    assert Settings.load(str(p)).volume == 0.8
    p.write_text('{"sound": false, "volume": 7}')
    s = Settings.load(str(p))
    assert (s.sound, s.volume) == (False, 1.0)
    p.write_text("[]")
    assert Settings.load(str(p)).sound is True


def test_save_into_a_missing_directory(tmp_path):
    s = Settings(str(tmp_path / "deep" / "settings.json"), volume=0.3)
    s.save()
    assert Settings.load(s.path).volume == 0.3
