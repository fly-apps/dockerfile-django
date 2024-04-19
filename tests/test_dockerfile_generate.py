import re
import os
from unittest.mock import patch

from typer.testing import CliRunner
from dockerfile_django.main import cli
import pytest

from tests.utils import copy_dir_to_tmp_path, PYTHON_VERSION

runner = CliRunner()

PYTHON_NOT_SUPPORTED = "3.7.17"
PYTHON_SUPPORTED = "3.11.4"  # make sure to keep this updated to a supported version
PYTHON_PINNED = "3.10.0b1"

TEST_CASE_DIR = "tests/test_cases/"

ARG_MASK = re.compile(r"^(ARG\s+\w+\s*=).*?(\s*\\?)$", re.MULTILINE)

def get_scenario_dirs():
    scenario_dirs = []

    for test_folder in os.listdir(TEST_CASE_DIR):
        if test_folder == "dockerfile_aborted":
            continue
        test_folder_path = os.path.join(TEST_CASE_DIR, test_folder)
        if os.path.isdir(test_folder_path):
            for specific_dir in os.listdir(test_folder_path):
                specific_dir_path = os.path.join(test_folder_path, specific_dir)
                if os.path.isdir(specific_dir_path):
                    scenario_dirs.append(specific_dir_path)
    return scenario_dirs


@pytest.mark.parametrize("scenario_dir", get_scenario_dirs())
def test_dockerfile_generation(scenario_dir, tmp_path):
    with patch("platform.python_version", return_value=PYTHON_VERSION):
        copy_dir_to_tmp_path(scenario_dir, tmp_path)

        result = runner.invoke(cli, ["generate", "--dir", f"{tmp_path}", "--force"])

        expected_dockerfile_path = os.path.join(scenario_dir, "Dockerfile")

        generated_dockerfile_path = tmp_path / "Dockerfile"

        with open(generated_dockerfile_path, "r") as file:
            generated_dockerfile_contents = ARG_MASK.sub(r"\1xxx\2", file.read())

        if 'TEST_CAPTURE' in os.environ:
            with open(expected_dockerfile_path, "w") as file:
                file.write(generated_dockerfile_contents)

        with open(expected_dockerfile_path, "r") as file:
            expected_dockerfile_contents = ARG_MASK.sub(r"\1xxx\2", file.read())

        assert (
            generated_dockerfile_contents == expected_dockerfile_contents
        ), f"Mismatch in Dockerfile for {scenario_dir}"

        assert result.exit_code == 0


def test_generate_not_supported_python():
    with patch("platform.python_version", return_value=PYTHON_NOT_SUPPORTED):
        result = runner.invoke(
            cli, ["generate", "--dir", "tests/test_cases/dockerfile_aborted/scenario_2"]
        )
        assert result.exit_code == 1
        assert (
            f"[WARNING] It looks like you have Python {PYTHON_NOT_SUPPORTED} installed, but it has reached its "
            f"end of support." in result.stdout
        )


def test_generate_supported_python():
    with patch("platform.python_version", return_value=PYTHON_SUPPORTED):
        result = runner.invoke(
            cli, ["generate", "--dir", "tests/test_cases/dockerfile_aborted/scenario_2"]
        )
        assert result.exit_code == 1
        assert f"[INFO] Python {PYTHON_SUPPORTED} was detected." in result.stdout


def test_generate_pinned_supported_python():
    with patch("platform.python_version", return_value=PYTHON_PINNED):
        result = runner.invoke(
            cli, ["generate", "--dir", "tests/test_cases/dockerfile_aborted/scenario_2"]
        )
        assert result.exit_code == 1
        assert (
            f"[WARNING] It looks like you have Python {PYTHON_PINNED} installed, which is not an official "
            f"release." in result.stdout
        )
