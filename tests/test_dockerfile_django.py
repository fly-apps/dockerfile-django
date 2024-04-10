from typer.testing import CliRunner
from dockerfile_django.main import cli


runner = CliRunner()


def test_welcome():
    result = runner.invoke(cli, ["welcome"])
    assert result.exit_code == 0
    assert f"Welcome to Dockerfile Generator for Django projects" in result.stdout
