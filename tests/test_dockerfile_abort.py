from unittest.mock import patch

from typer.testing import CliRunner
from dockerfile_django.main import cli
from tests.utils import PYTHON_VERSION

runner = CliRunner()

PYTHON_NOT_SUPPORTED = "3.7.17"
PYTHON_SUPPORTED = "3.11.4"  # make sure to keep this updated to a supported version
PYTHON_PINNED = "3.10.0b1"


def test_generate_not_supported_python():
    with patch("platform.python_version") as mock_version:
        mock_version.return_value = PYTHON_NOT_SUPPORTED
        result = runner.invoke(
            cli, ["generate", "--dir", "tests/test_cases/dockerfile_aborted/scenario_2"]
        )
        assert result.exit_code == 1
        assert (
            f"[WARNING] It looks like you have Python {PYTHON_NOT_SUPPORTED} installed, but it has reached its "
            f"end of support." in result.stdout
        )


def test_generate_supported_python():
    with patch("platform.python_version") as mock_version:
        mock_version.return_value = PYTHON_SUPPORTED
        result = runner.invoke(
            cli, ["generate", "--dir", "tests/test_cases/dockerfile_aborted/scenario_2"]
        )
        assert result.exit_code == 1
        assert f"[INFO] Python {PYTHON_SUPPORTED} was detected." in result.stdout


def test_generate_pinned_supported_python():
    with patch("platform.python_version") as mock_version:
        mock_version.return_value = PYTHON_PINNED
        result = runner.invoke(
            cli, ["generate", "--dir", "tests/test_cases/dockerfile_aborted/scenario_2"]
        )
        assert result.exit_code == 1
        assert (
            f"[WARNING] It looks like you have Python {PYTHON_PINNED} installed, which is not an official "
            f"release." in result.stdout
        )


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
