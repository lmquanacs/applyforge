from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from career_ai.cli import app

runner = CliRunner()


def test_init(tmp_path):
    with patch("career_ai.cli.init_config", return_value=tmp_path / "config.yaml") as mock:
        result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    mock.assert_called_once()


def test_review_dry_run(tmp_path):
    cv = tmp_path / "cv.txt"
    cv.write_text("Senior Python Engineer at Acme Corp. 5 years experience.")

    with patch("career_ai.cli.call_llm", side_effect=SystemExit(0)):
        result = runner.invoke(app, ["review", str(cv), "--dry-run"])
    assert result.exit_code == 0


def test_write_dry_run(tmp_path):
    cv = tmp_path / "cv.txt"
    cv.write_text("Python Engineer. Built REST APIs.")
    jd = tmp_path / "jd.txt"
    jd.write_text("We need a Python developer with REST API experience.")

    with patch("career_ai.cli.call_llm", side_effect=SystemExit(0)):
        result = runner.invoke(app, ["write", str(cv), "--jd", str(jd), "--dry-run"])
    assert result.exit_code == 0
