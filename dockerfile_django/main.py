import re
from enum import Enum
from typing import Optional

import typer
import os
import platform
from pathlib import Path
from packaging import version
from jinja2 import Environment, FileSystemLoader

from pydantic import BaseModel

from dockerfile_django.utils import (
    find_files,
    check_for_keyword_in_file,
    get_random_secret_key,
    find_file_same_dir,
    extract_secret_key_from_dockerfile,
    colorize_diff,
)


cli = typer.Typer()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

PYTHON_LATEST_SUPPORTED_VERSION = "3.8.0"
PYTHON_LATEST_RELEASED_VERSION = "3.12.0"
DEFAULT_PYTHON_VERSION = "3.12"


class DependencyManagerPackageEnum(str, Enum):
    pipenv = "pipenv"
    poetry = "poetry"
    pip = "pip"


class DatabaseEnum(str, Enum):
    no_db = "no_db"
    sqlite = "sqlite"
    postgres = "postgres"
    mysql = "mysql"
    oracle = "oracle"


class ServerTypeEnum(str, Enum):
    wsgi = "wsgi"
    asgi = "asgi"


class ServerEnum(str, Enum):
    gunicorn = "gunicorn"
    daphne = "daphne"
    hypercorn = "hypercorn"
    uvicorn = "uvicorn"
    granian = "granian"


class DependencyConfig(BaseModel):
    manager: DependencyManagerPackageEnum = DependencyManagerPackageEnum.pip
    dependency_file_name: str = "requirements.txt"
    server: ServerEnum = ServerEnum.gunicorn
    database: DatabaseEnum = DatabaseEnum.no_db


class SettingsConfig(BaseModel):
    settings_files: list[Path]
    has_collectstatic: bool = False
    has_random_secret_key: bool = False
    random_secret_key: Optional[str] = None


class OtherConfig(BaseModel):
    project_name: str
    server_type: ServerTypeEnum = ServerTypeEnum.wsgi


class DjangoProjectConfig(BaseModel):
    dir: str = "."
    python_version: str = DEFAULT_PYTHON_VERSION
    is_python_version_pinned: bool = False
    dependency_config: DependencyConfig
    settings_config: SettingsConfig
    config: OtherConfig


class DjangoProjectExtractor:
    """
    Extractor for Django project config info.
    """

    def __init__(self, python_version: str, directory: str = ".") -> None:
        self.directory = directory
        self.python_version = python_version

    def extract_project_info(self) -> DjangoProjectConfig:
        python_partial_version, pinned = (
            (self.python_version, False) if self.python_version else get_python_info()
        )
        settings_config = get_settings_config(self.directory)
        dependency_config = get_dependency_config(self.directory)
        config = get_project_config(self.directory)

        return DjangoProjectConfig(
            dir=self.directory,
            python_version=python_partial_version,
            settings_config=settings_config,
            dependency_config=dependency_config,
            config=config,
            is_pinned=pinned,
        )


def get_server_info(dependency_file: str) -> ServerEnum:
    """
    Get the server info from the dependency file.

    :param dependency_file:
    :return: The server type.
    """
    if check_for_keyword_in_file(
        dependency_file, "uvicorn", "#"
    ) and check_for_keyword_in_file(dependency_file, "gunicorn", "#"):
        server = ServerEnum.uvicorn
        typer.secho(
            f"[INFO] Uvicorn Web Server was found in {dependency_file}",
            fg=typer.colors.GREEN,
        )
    elif check_for_keyword_in_file(dependency_file, "gunicorn", "#"):
        server = ServerEnum.gunicorn
        typer.secho(
            f"[INFO] Gunicorn Web Server was found in {dependency_file}",
            fg=typer.colors.GREEN,
        )
    elif check_for_keyword_in_file(dependency_file, "daphne", "#"):
        server = ServerEnum.daphne
        typer.secho(
            f"[INFO] Daphne Web Server was found in {dependency_file}",
            fg=typer.colors.GREEN,
        )
    elif check_for_keyword_in_file(dependency_file, "hypercorn", "#"):
        server = ServerEnum.hypercorn
        typer.secho(
            f"[INFO] Hypercorn Web Server was found in {dependency_file}",
            fg=typer.colors.GREEN,
        )
    elif check_for_keyword_in_file(dependency_file, "granian", "#"):
        server = ServerEnum.granian
        typer.secho(
            f"[INFO] Granian Web Server was found in {dependency_file}",
            fg=typer.colors.GREEN,
        )
    else:
        server = ServerEnum.gunicorn
        typer.secho(
            f"[WARNING] No known Web Server was found in {dependency_file}. Gunicorn Web Server is used instead."
            f"Make sure to update the generated Dockerfile with the correct Web Server.",
            fg=typer.colors.YELLOW,
        )
    return server


def get_database_info(dependency_file: str) -> DatabaseEnum:
    """
    Get the database info from the dependency file.

    :param dependency_file:
    :return: The database type.
    """
    typer.secho(
        f"[INFO] Check for DATABASE in {dependency_file}", fg=typer.colors.GREEN
    )
    if check_for_keyword_in_file(
        dependency_file, "psycopg", "#"
    ) or check_for_keyword_in_file(dependency_file, "psycopg2", "#"):
        database = DatabaseEnum.postgres
        typer.secho(
            f"[INFO] Postgres was found in {dependency_file}", fg=typer.colors.GREEN
        )
    # TODO: Add more database checks (e.g. sqlite, mysql, oracle, etc.)
    else:
        typer.secho(
            "[WARNING] No known database was found.",
            fg=typer.colors.YELLOW,
        )
        database = DatabaseEnum.no_db
    return database


def get_dependency_config(directory: str = ".") -> DependencyConfig:
    """
    Extract the dependency manager from the directory path.

    :param directory: The directory path.
    :return: The dependency manager.
    """
    if find_file_same_dir("Pipfile", directory):
        dependency_manager = DependencyManagerPackageEnum.pipenv
        dependency_file = "Pipfile"
        typer.secho("[INFO] 'Pipfile' was found.", fg=typer.colors.GREEN)
    elif find_file_same_dir("pyproject.toml", directory):
        dependency_manager = DependencyManagerPackageEnum.poetry
        dependency_file = "pyproject.toml"
        typer.secho("[INFO] 'pyproject.toml' was found.", fg=typer.colors.GREEN)
    elif find_file_same_dir("requirements.txt", directory):
        dependency_manager = DependencyManagerPackageEnum.pip
        dependency_file = "requirements.txt"
        typer.secho("[INFO] 'requirements.txt' was found.", fg=typer.colors.GREEN)
    else:
        typer.secho(
            "[WARNING] No dependency file was found. 'requirements.txt' is used instead.",
            fg=typer.colors.YELLOW,
        )
        dependency_manager = DependencyManagerPackageEnum.pip
        dependency_file = "requirements.txt"

    database = get_database_info(f"{directory}/{dependency_file}")

    server = get_server_info(f"{directory}/{dependency_file}")

    return DependencyConfig(
        manager=dependency_manager,
        dependency_file_name=dependency_file,
        database=database,
        server=server,
    )


def get_dockerfile(directory: str = ".") -> bool:
    """
    Find the Dockerfile in the directory.

    :param directory: The directory path.
    :return: The Dockerfile path.
    """
    if find_file_same_dir("Dockerfile", directory):
        return True
    return False


def get_settings_config(directory: str = ".") -> SettingsConfig:
    """
    Extract config of the 'settings.py' file from the directory path.

    :param directory: The directory path.
    :return: The settings file.
    """
    settings_files = find_settings_files(directory)

    if len(settings_files) > 1:
        typer.secho(
            f"[WARNING] Multiple 'settings.py' files were found in your Django project: ",
            fg=typer.colors.YELLOW,
        )
        typer.secho(
            f"{', '.join(str(settings_file) for settings_file in settings_files)}",
            fg=typer.colors.BLUE,
        )
        typer.secho(
            f"[WARNING] It's not recommended to have multiple 'settings.py' files. "
            f"Instead, you can have a 'settings/' directory with the settings files according to the different "
            f"environments (e.g. local.py, staging.py, production.py). "
            f"In this case, you can specify which settings file to use when running the Django project by "
            f"setting the 'DJANGO_SETTINGS_MODULE' environment variable to the corresponding settings file.",
            fg=typer.colors.YELLOW,
        )

    settings_file = settings_files[0]
    typer.secho(
        f"[INFO] Extracting config from '{settings_file}'", fg=typer.colors.GREEN
    )

    has_collectstatic = check_for_keyword_in_file(settings_file, "STATIC_ROOT", "#")

    has_random_secret_key = check_for_keyword_in_file(
        settings_file, "get_random_secret_key()", "#"
    )
    existing_dockerfile = get_dockerfile(directory)

    # If Dockerfile already exists and has a random secret key, extract it.
    if existing_dockerfile and not has_random_secret_key:
        dockerfile_path = Path(f"{directory}/Dockerfile")
        random_secret_key = extract_secret_key_from_dockerfile(dockerfile_path)
        if not random_secret_key:
            random_secret_key = get_random_secret_key(50)
    elif not has_random_secret_key:
        random_secret_key = get_random_secret_key(50)
        typer.secho(
            f"[INFO] A random secret key was generated for the Dockerfile",
            fg=typer.colors.GREEN,
        )
    else:
        random_secret_key = None

    return SettingsConfig(
        settings_files=settings_files,
        has_collectstatic=has_collectstatic,
        has_random_secret_key=has_random_secret_key,
        random_secret_key=random_secret_key,
    )


def get_project_config(directory: str = ".") -> OtherConfig:
    """
    Extract other config of the project from the directory path.

    :param directory: The directory path.
    :return: The server type and project name.
    """
    wsgi_found = False
    asgi_found = False
    wsgi_files, asgi_files = find_server_files(directory)

    if wsgi_files:
        wsgi_found = True
        wsgi_name = wsgi_files[0].parent.name
        if len(wsgi_files) > 1:
            typer.secho(
                f"[WARNING] Multiple 'wsgi.py' files were found in your Django project: ",
                fg=typer.colors.YELLOW,
            )
            typer.secho(
                f"{', '.join(str(wsgi_file) for wsgi_file in wsgi_files)}",
                fg=typer.colors.BLUE,
            )
            typer.secho(
                f"[WARNING] Before proceeding, make sure '{wsgi_name}' is the module containing a "
                f"WSGI application object named 'application'. If not, update your Dockefile.",
                fg=typer.colors.YELLOW,
            )

    if asgi_files:
        asgi_found = True
        asgi_name = asgi_files[0].parent.name
        if len(asgi_files) > 1:
            typer.secho(
                f"[WARNING] Multiple 'asgi.py' files were found in your Django project: ",
                fg=typer.colors.YELLOW,
            )
            typer.secho(
                f"{', '.join(str(asgi_file) for asgi_file in asgi_files)}",
                fg=typer.colors.BLUE,
            )
            typer.secho(
                f"[WARNING] Before proceeding, make sure '{asgi_name}' is the module containing a "
                f"ASGI application object named 'application'. If not, update your Dockefile.",
                fg=typer.colors.YELLOW,
            )

    if wsgi_found and asgi_found:
        typer.secho(
            f"[WARNING] Both 'wsgi.py' and 'asgi.py' files were found in your Django project.",
            fg=typer.colors.YELLOW,
        )
        settings_files = find_settings_files(directory)
        settings_file = settings_files[0]
        if check_for_keyword_in_file(settings_file, "WSGI_APPLICATION", "#"):
            asgi_found = False
            typer.secho(
                f"[WARNING] 'WSGI_APPLICATION' setting was found in your 'settings.py' file. Using WSGI server in the "
                f"Dockerfile. If that's not correct, make sure to update your Dockerfile to use an ASGI server.",
                fg=typer.colors.YELLOW,
            )
        if check_for_keyword_in_file(settings_file, "ASGI_APPLICATION", "#"):
            wsgi_found = False
            typer.secho(
                f"[WARNING] 'ASGI_APPLICATION' setting was found in your 'settings.py' file. Using WSGI server in the "
                f"Dockerfile. If that's not correct, make sure to update your Dockerfile to use a WSGI server.",
                fg=typer.colors.YELLOW,
            )
    elif not wsgi_found and not asgi_found:
        typer.secho(
            "[ERROR] No 'wsgi.py' or 'asgi.py' files were found.", fg=typer.colors.RED
        )
        raise typer.Abort()

    return OtherConfig(
        server_type=ServerTypeEnum.wsgi if wsgi_found else ServerTypeEnum.asgi,
        project_name=asgi_name if asgi_found else wsgi_name if wsgi_found else "demo",
    )


def get_python_info() -> tuple[str, bool]:
    """
    Get the Python version and check if it is pinned.

    :return: The Python version and whether it is pinned. Default to the latest supported version.
    """
    version_str = platform.python_version()

    version_regex = r"^(\d+)\.(\d+)\.(\d+)"

    match = re.match(version_regex, version_str)

    if match:
        major, minor, patchlevel = match.groups()
        full_version = f"{major}.{minor}.{patchlevel}"

        # Check if version is pinned like in "3.12.0b4"
        is_pinned = bool(re.search(r"[^\d.]", version_str))

        current_version = version.parse(full_version)
        latest_supported_version = version.parse(PYTHON_LATEST_SUPPORTED_VERSION)

        if current_version < latest_supported_version:
            typer.secho(
                f"[WARNING] It looks like you have Python {version_str} installed, but it has reached its "
                f"end of support. Using Python {PYTHON_LATEST_SUPPORTED_VERSION} to build your image instead."
                f"Make sure to update the Dockerfile to use an image that is compatible with the Python "
                f"version you are using. We highly recommend that you update your application to use Python "
                f"{PYTHON_LATEST_SUPPORTED_VERSION} or newer. "
                f"(https://devguide.python.org/versions/#supported-versions)",
                fg=typer.colors.YELLOW,
            )
            major, minor = DEFAULT_PYTHON_VERSION.split(".")
            partial_version = f"{major}.{minor}"
        else:
            partial_version = f"{major}.{minor}"

        if is_pinned:
            typer.secho(
                f"[WARNING] It looks like you have Python {version_str} installed, which is not an official "
                f"release. This version is being explicitly pinned in the generated Dockerfile, and should be "
                f"changed to an official release before deploying to production.",
                fg=typer.colors.YELLOW,
            )
        else:
            typer.secho(
                f"[INFO] Python {version_str} was detected. 'python:{partial_version}-slim-bullseye'"
                f" image will be set in the Dockerfile.",
                fg=typer.colors.GREEN,
            )

        return partial_version, is_pinned
    else:
        return DEFAULT_PYTHON_VERSION.split("."), False


def find_server_files(start_path: str = ".") -> tuple[list[Path], list[Path]]:
    """
    Search for 'wsgi.py.py' and 'asgi.py' files starting from 'start_path',
    excluding any paths that contain 'site-packages'.

    :param start_path: The directory to start the search from.
    :return: A tuple of lists containing Path objects pointing to 'wsgi.py' and 'asgi.py' files.
    """
    wsgi_files = find_files("wsgi.py", start_path)
    asgi_files = find_files("asgi.py", start_path)

    if not (wsgi_files or asgi_files):
        typer.secho(
            "[ERROR] No 'wsgi.py' or 'asgi.py' files were found.", fg=typer.colors.RED
        )
    return wsgi_files, asgi_files


def find_settings_files(start_path: str = ".") -> list[Path]:
    """
    Search for 'settings.py' files starting from 'start_path',
    excluding any paths that contain 'site-packages'.

    :param start_path: The directory to start the search from.
    :return: A list of Path objects pointing to 'settings.py' files.
    """
    settings_files = find_files("*settings*.py", start_path)
    if not settings_files:
        settings_files = find_files("*settings/*prod*.py", start_path)
        if not settings_files:
            typer.secho(
                "[ERROR] No 'settings.py' files were found.", fg=typer.colors.RED
            )
            raise typer.Abort()

    for file in settings_files:
        if file.name == "settings.py":
            return [Path(file)]

    return settings_files


class DockerfileGenerator:
    """
    Dockerfile Generator for Django projects.
    """

    def __init__(
        self, project_info: DjangoProjectConfig, force: bool = False, diff: bool = False
    ) -> None:
        self.project_info = project_info
        self.force = force
        self.diff = diff

    def run(self) -> None:
        templates = {
            "Dockerfile.jinja": "Dockerfile",
        }

        for template_name, output_name in templates.items():
            self.render_and_write_template(template_name, output_name)

    def render_and_write_template(self, template_name: str, output_name: str) -> None:
        typer.secho(f"[INFO] Generating {output_name}...", fg=typer.colors.GREEN)
        env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=True,
        )
        template = env.get_template(template_name)
        generated_content = template.render(
            dj=self.project_info,
        )

        output_path = os.path.join(self.project_info.dir, output_name)

        if os.path.exists(output_path) and not self.force:
            with open(output_path, "r") as f:
                existing_content = f.readlines()

            generated_lines = generated_content.splitlines(keepends=True)

            if self.diff:
                typer.secho(f"[INFO] Diff {output_name}\n", fg=typer.colors.GREEN)
                if existing_content == generated_lines:
                    typer.secho(
                        f"[INFO] Identical {output_name}\n", fg=typer.colors.GREEN
                    )
                else:
                    colorize_diff(output_name, existing_content, generated_lines)
                return
            elif existing_content == generated_lines:
                typer.secho(f"[INFO] Identical {output_name}\n", fg=typer.colors.GREEN)
                return

            typer.secho(
                f"[WARNING] Conflict {output_name}\n",
                fg=typer.colors.YELLOW,
                bold=True,
                nl=True,
            )
            colorize_diff(output_name, existing_content, generated_lines)

            if not (
                self.force
                or typer.confirm(
                    typer.style("\nOverwrite?", fg=typer.colors.YELLOW, bold=True)
                )
            ):
                typer.echo(f"[INFO] Skip overwriting the existing {output_name}...")
                return

        with open(output_path, "w") as f:
            f.write(generated_content)
            typer.secho(
                f"[INFO] Generated '{output_path}' was saved successfully!",
                fg=typer.colors.GREEN,
            )


@cli.command()
def generate(
    directory: str = typer.Option(
        ".", "--dir", help="The directory to search for Django project files"
    ),
    force: bool = typer.Option(
        False, "--force", help="Force overwriting the existing Dockerfile"
    ),
    diff: bool = typer.Option(
        False,
        "--diff",
        help="Display differences between current and generated Dockerfile",
    ),
    python_version: str = typer.Option(
        None, "--pyver", help="Python version to use in the Dockerfile"
    ),
):
    """
    Generate a Dockerfile for Django projects.
    """
    typer.secho(
        "🐳🦄✨ Welcome to Dockerfile Generator for Django projects ✨🦄🐳",
        fg=typer.colors.MAGENTA,
    )
    typer.secho(
        f"[INFO] Extracting Django project config info from '{directory}'",
        fg=typer.colors.GREEN,
    )
    django_project = DjangoProjectExtractor(python_version, directory)
    django_project_info = django_project.extract_project_info()
    generator = DockerfileGenerator(django_project_info, force, diff)
    generator.run()


@cli.command()
def welcome():
    """
    Display a welcome message.
    """
    typer.echo("🐳🦄✨ Welcome to Dockerfile Generator for Django projects ✨🦄🐳")
    typer.echo("Usage: dockerfile-django [COMMAND]")
    typer.echo("Commands:")
    typer.echo("  welcome         Display a welcome message")
    typer.echo("  generate        Generate a Dockerfile for Django projects")
    typer.echo(
        "Run 'dockerfile-django [COMMAND] --help' for more information on a specific command."
    )
