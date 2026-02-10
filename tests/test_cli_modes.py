from click.testing import CliRunner

from code_tutor.cli import main


def test_root_help_lists_roguelike_and_exercise_alias():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "roguelike" in result.output
    assert "exercise" in result.output


def test_roguelike_and_exercise_help_share_commands():
    runner = CliRunner()
    roguelike_help = runner.invoke(main, ["roguelike", "--help"])
    exercise_help = runner.invoke(main, ["exercise", "--help"])

    assert roguelike_help.exit_code == 0
    assert exercise_help.exit_code == 0
    assert "show" in roguelike_help.output
    assert "grade" in roguelike_help.output
    assert "show" in exercise_help.output
    assert "grade" in exercise_help.output
