import os
from unittest.mock import patch

from typer.testing import CliRunner
from dockerfile_django.main import cli
import pytest

from tests.utils import copy_dir_to_tmp_path, PYTHON_VERSION

runner = CliRunner()


def get_scenario_dirs():
    base_dir = "tests/test_cases/"
    scenario_dirs = []

    for test_folder in os.listdir(base_dir):
        if test_folder == "dockerfile_aborted":
            continue
        test_folder_path = os.path.join(base_dir, test_folder)
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

        with open(expected_dockerfile_path, "r") as file:
            expected_dockerfile_contents = file.read()

        with open(generated_dockerfile_path, "r") as file:
            generated_dockerfile_contents = file.read()

        assert (
            generated_dockerfile_contents == expected_dockerfile_contents
        ), f"Mismatch in Dockerfile for {scenario_dir}"

        assert result.exit_code == 0
