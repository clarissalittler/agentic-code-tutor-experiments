from code_tutor.modes import COMMAND_ALIASES, get_all_modes, get_core_modes


def test_core_modes_include_roguelike():
    commands = [mode.command for mode in get_core_modes()]
    assert commands == ["review", "teach-me", "roguelike"]


def test_all_modes_include_proof_group():
    commands = [mode.command for mode in get_all_modes()]
    assert "proof" in commands


def test_exercise_alias_points_to_roguelike():
    assert COMMAND_ALIASES["exercise"] == "roguelike"
