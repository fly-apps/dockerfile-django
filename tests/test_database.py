import os
from unittest.mock import patch

from typer.testing import CliRunner
from dockerfile_django.main import cli
import pytest

from tests.utils import copy_dir_to_tmp_path, PYTHON_VERSION

runner = CliRunner()


def get_scenario_dirs():
    base_dir = "tests/test_cases/database/"
    return [
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
    ]


@pytest.mark.parametrize("scenario_dir", get_scenario_dirs())
def test_dockerfile_generation(scenario_dir, tmp_path):
    with patch("platform.python_version", return_value=PYTHON_VERSION):
        # Copy the scenario directory to a temporary directory
        copy_dir_to_tmp_path(scenario_dir, tmp_path)

        result = runner.invoke(cli, ["generate", "--dir", f"{tmp_path}", "--force"])

        # The expected Dockerfile is still in 'scenario_dir', also named 'Dockerfile'
        expected_dockerfile_path = os.path.join(scenario_dir, "Dockerfile")

        # The generated Dockerfile will be in 'tmp_path', named 'Dockerfile'
        generated_dockerfile_path = tmp_path / "Dockerfile"

        with open(expected_dockerfile_path, "r") as file:
            expected_dockerfile_contents = file.read()

        with open(generated_dockerfile_path, "r") as file:
            generated_dockerfile_contents = file.read()

        # Assert to compare the generated Dockerfile in 'tmp_path' with the expected one in 'scenario_dir'
        assert (
            generated_dockerfile_contents == expected_dockerfile_contents
        ), f"Mismatch in Dockerfile for {scenario_dir}"

        assert result.exit_code == 0
