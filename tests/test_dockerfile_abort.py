from unittest.mock import patch

from typer.testing import CliRunner
from dockerfile_django.main import cli
from tests.utils import PYTHON_VERSION

runner = CliRunner()


def test_generate_no_settings_found():
    with patch("platform.python_version", return_value=PYTHON_VERSION):
        result = runner.invoke(
            cli, ["generate", "--dir", "tests/test_cases/dockerfile_aborted/scenario_1"]
        )
        assert result.exit_code == 1
        assert f"[ERROR] No 'settings.py' files were found." in result.stdout


def test_generate_no_wsgi_asgi_found():
    with patch("platform.python_version", return_value=PYTHON_VERSION):
        result = runner.invoke(
            cli, ["generate", "--dir", "tests/test_cases/dockerfile_aborted/scenario_2"]
        )
        assert result.exit_code == 1
        assert f"[ERROR] No 'wsgi.py' or 'asgi.py' files were found." in result.stdout
