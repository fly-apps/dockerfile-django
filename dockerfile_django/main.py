import toml
import re
from enum import Enum
from typing import Optional

import typer
import os
import platform
from pathlib import Path
from packaging import version
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.table import Table

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

console = Console()

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
    dir: Path = Path(".")
    python_version: str = DEFAULT_PYTHON_VERSION
    is_python_version_pinned: bool = False
    dependency_config: DependencyConfig
    settings_config: SettingsConfig
    config: OtherConfig


class DjangoProjectExtractor:
    """
    Extractor for Django project config info.
    """

    def __init__(self, python_version: str, dir: Path = Path(".")) -> None:
        self.dir = dir
        self.python_version = python_version

    def extract_project_info(self) -> DjangoProjectConfig:
        python_partial_version, pinned = get_python_info(self.python_version)
        settings_config = get_settings_config(self.dir)
        dependency_config = get_dependency_config(self.dir)
        config = get_project_config(self.dir)

        return DjangoProjectConfig(
            dir=self.dir,
            python_version=python_partial_version,
            settings_config=settings_config,
            dependency_config=dependency_config,
            config=config,
            is_pinned=pinned,
        )


def get_server_info(dependency_file: Path) -> ServerEnum:
    """
    Get the server info from the dependency file.

    :param dependency_file:
    :return: The server type.
    """
    if check_for_keyword_in_file(
        dependency_file, "uvicorn", "#"
    ) and check_for_keyword_in_file(dependency_file, "gunicorn", "#"):
        server = ServerEnum.uvicorn
        console.print(
            f"[INFO] Uvicorn Web Server was found in '{dependency_file}'"
        )
    elif check_for_keyword_in_file(dependency_file, "gunicorn", "#"):
        server = ServerEnum.gunicorn
        console.print(
            f"[INFO] Gunicorn Web Server was found in '{dependency_file}'"
        )
    elif check_for_keyword_in_file(dependency_file, "daphne", "#"):
        server = ServerEnum.daphne
        console.print(
            f"[INFO] Daphne Web Server was found in '{dependency_file}'"
        )
    elif check_for_keyword_in_file(dependency_file, "hypercorn", "#"):
        server = ServerEnum.hypercorn
        console.print(
            f"[INFO] Hypercorn Web Server was found in '{dependency_file}'"
        )
    elif check_for_keyword_in_file(dependency_file, "granian", "#"):
        server = ServerEnum.granian
        console.print(
            f"[INFO] Granian Web Server was found in '{dependency_file}'"
        )
    else:
        server = ServerEnum.gunicorn
        console.print(
            f"[WARNING] No known Web Server was found in '{dependency_file}'. Gunicorn Web Server is used instead."
            f"Make sure to update the generated Dockerfile with the correct Web Server.",
            style="yellow",
        )
    return server


def get_database_info(dependency_file: Path) -> DatabaseEnum:
    """
    Get the database info from the dependency file.

    :param dependency_file:
    :return: The database type.
    """
    console.print(
        f"[INFO] Check for database in '{dependency_file}'"
    )
    if check_for_keyword_in_file(
        dependency_file, "psycopg", "#"
    ) or check_for_keyword_in_file(dependency_file, "psycopg2", "#"):
        database = DatabaseEnum.postgres
        console.print(
            f"[INFO] Postgres was found in '{dependency_file}'"
        )
    # TODO: Add more database checks (e.g. sqlite, mysql, oracle, etc.)
    else:
        console.print(
            "[WARNING] No known database was found.",
            style="yellow",
        )
        database = DatabaseEnum.no_db
    return database


def get_dependency_config(dir: Path = Path(".")) -> DependencyConfig:
    """
    Extract the dependency manager from the directory path.

    :param dir: The directory path.
    :return: The dependency manager.
    """
    if find_file_same_dir("requirements.txt", dir):
        dependency_manager = DependencyManagerPackageEnum.pip
        dependency_file = "requirements.txt"
        console.print("[INFO] 'requirements.txt' was found.")
    elif find_file_same_dir("Pipfile", dir):
        dependency_manager = DependencyManagerPackageEnum.pipenv
        dependency_file = "Pipfile"
        console.print("[INFO] 'Pipfile' was found.")
    elif find_file_same_dir("pyproject.toml", dir):
        dependency_manager = DependencyManagerPackageEnum.poetry
        dependency_file = "pyproject.toml"
        console.print("[INFO] 'pyproject.toml' was found.")
    else:
        console.print(
            "[WARNING] No dependency file was found. 'requirements.txt' is used instead.",
            style="yellow",
        )
        dependency_manager = DependencyManagerPackageEnum.pip
        dependency_file = "requirements.txt"

    database = get_database_info(dir / dependency_file)

    server = get_server_info(dir / dependency_file)

    return DependencyConfig(
        manager=dependency_manager,
        dependency_file_name=dependency_file,
        database=database,
        server=server,
    )


def get_dockerfile(dir: Path = Path(".")) -> bool:
    """
    Find the Dockerfile in the directory.

    :param dir: The directory path.
    :return: The Dockerfile path.
    """
    if find_file_same_dir("Dockerfile", dir):
        return True
    return False


def get_settings_config(dir: Path = Path(".")) -> SettingsConfig:
    """
    Extract config of the 'settings.py' file from the directory path.

    :param dir: The directory path.
    :return: The settings file.
    """
    settings_files, closest_settings = find_settings_files(dir)

    if len(settings_files) > 1:
        console.print(
            f"[WARNING] Multiple 'settings.py' files were found in your Django project: ",
            style="yellow",
        )
        console.print(
            f"{', '.join(str(settings_file) for settings_file in settings_files)}",
            style="blue",
        )
        console.print(
            f"[WARNING] It's not recommended to have multiple 'settings.py' files. "
            f"Instead, you can have a 'settings/' directory with the settings files according to the different "
            f"environments (e.g. local.py, staging.py, production.py). "
            f"In this case, you can specify which settings file to use when running the Django project by "
            f"setting the 'DJANGO_SETTINGS_MODULE' environment variable to the corresponding settings file.",
            style="yellow",
        )

    # settings_file = settings_files[0]
    console.print(
        f"[INFO] Extracting config from '{closest_settings}'"
    )

    has_collectstatic = check_for_keyword_in_file(closest_settings, "STATIC_ROOT", "#")

    has_random_secret_key = check_for_keyword_in_file(
        closest_settings, "get_random_secret_key()", "#"
    )
    existing_dockerfile = get_dockerfile(dir)

    # If Dockerfile already exists and has a random secret key, extract it.
    if existing_dockerfile and not has_random_secret_key:
        dockerfile_path = Path(f"{dir}/Dockerfile")
        random_secret_key = extract_secret_key_from_dockerfile(dockerfile_path)
        if not random_secret_key:
            random_secret_key = get_random_secret_key(50)
    elif not has_random_secret_key:
        random_secret_key = get_random_secret_key(50)
        console.print(
            f"[INFO] A random secret key was generated for the Dockerfile"
        )
    else:
        random_secret_key = None

    return SettingsConfig(
        settings_files=settings_files,
        has_collectstatic=has_collectstatic,
        has_random_secret_key=has_random_secret_key,
        random_secret_key=random_secret_key,
    )


def get_project_config(dir: Path = Path(".")) -> OtherConfig:
    """
    Extract other config of the project from the directory path.

    :param dir: The directory path.
    :return: The server type and project name.
    """
    wsgi_found = False
    asgi_found = False
    wsgi_files, closest_wsgi, asgi_files, closest_asgi = find_server_files(dir)

    if wsgi_files:
        wsgi_found = True
        wsgi_name = closest_wsgi.parent.name
        if len(wsgi_files) > 1:
            console.print(
                f"[WARNING] Multiple 'wsgi.py' files were found in your Django project: ",
                style="yellow",
            )
            console.print(
                f"{', '.join(str(wsgi_file) for wsgi_file in wsgi_files)}",
                style="blue",
            )
            console.print(
                f"[WARNING] Before proceeding, make sure '{wsgi_name}' is the module containing a "
                f"WSGI application object named 'application'. If not, update your Dockefile.",
                style="yellow",
            )

    if asgi_files:
        asgi_found = True
        asgi_name = closest_asgi.parent.name
        if len(asgi_files) > 1:
            console.print(
                f"[WARNING] Multiple 'asgi.py' files were found in your Django project: ",
                style="yellow",
            )
            console.print(
                f"{', '.join(str(asgi_file) for asgi_file in asgi_files)}",
                style="blue",
            )
            console.print(
                f"[WARNING] Before proceeding, make sure '{asgi_name}' is the module containing a "
                f"ASGI application object named 'application'. If not, update your Dockefile.",
                style="yellow",
            )

    if wsgi_found and asgi_found:
        console.print(
            f"[WARNING] Both 'wsgi.py' and 'asgi.py' files were found in your Django project.",
            style="yellow",
        )
        settings_files, closest_settings = find_settings_files(dir)
        if check_for_keyword_in_file(closest_settings, "WSGI_APPLICATION", "#"):
            asgi_found = False
            console.print(
                f"[WARNING] 'WSGI_APPLICATION' setting was found in your 'settings.py' file. Using WSGI server in the "
                f"Dockerfile. If that's not correct, make sure to update your Dockerfile to use an ASGI server.",
                style="yellow",
            )
        if check_for_keyword_in_file(closest_settings, "ASGI_APPLICATION", "#"):
            wsgi_found = False
            console.print(
                f"[WARNING] 'ASGI_APPLICATION' setting was found in your 'settings.py' file. Using WSGI server in the "
                f"Dockerfile. If that's not correct, make sure to update your Dockerfile to use a WSGI server.",
                style="yellow",
            )
    elif not wsgi_found and not asgi_found:
        console.print(
            "[ERROR] No 'wsgi.py' or 'asgi.py' files were found.", style="red"
        )
        raise typer.Abort()

    return OtherConfig(
        server_type=ServerTypeEnum.wsgi if wsgi_found else ServerTypeEnum.asgi,
        project_name=asgi_name if asgi_found else wsgi_name if wsgi_found else "demo",
    )


def get_python_info(python_version: str = None) -> tuple[str, bool]:
    """
    Get the Python version and check if it is pinned.

    :return: The Python version and whether it is pinned. Default to the latest supported version.
    """
    version_str = python_version or platform.python_version()

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
            console.print(
                f"[WARNING] It looks like you are using Python {version_str}, but it has reached its "
                f"end of support. Using Python {PYTHON_LATEST_SUPPORTED_VERSION} to build your image instead. "
                f"Make sure to update the Dockerfile to use an image that is compatible with the Python "
                f"version you are using. We highly recommend that you update your application to use Python "
                f"{PYTHON_LATEST_SUPPORTED_VERSION} or newer. "
                f"(https://devguide.python.org/versions/#supported-versions)",
                style="yellow",
            )
            major, minor = DEFAULT_PYTHON_VERSION.split(".")
            partial_version = f"{major}.{minor}"
        else:
            partial_version = f"{major}.{minor}"

        if is_pinned:
            console.print(
                f"[WARNING] It looks like you are using Python {version_str}, which is not an official "
                f"release. This version is being explicitly pinned in the generated Dockerfile, and should be "
                f"changed to an official release before deploying to production.",
                style="yellow",
            )
        else:
            console.print(
                f"[INFO] Python {version_str} was detected. 'python:{partial_version}-slim'"
                f" image will be set in the Dockerfile.",
            )

        return partial_version, is_pinned
    else:
        return DEFAULT_PYTHON_VERSION.split("."), False


def find_server_files(start_path: Path = Path(".")) -> tuple[list[Path], list[Path]]:
    """
    Search for 'wsgi.py.py' and 'asgi.py' files starting from 'start_path',
    excluding any paths that contain 'site-packages'.

    :param start_path: The directory to start the search from.
    :return: A tuple of lists containing Path objects pointing to 'wsgi.py' and 'asgi.py' files.
    """
    wsgi_files, closest_wsgi = find_files("wsgi.py", start_path)
    asgi_files, closest_asgi = find_files("asgi.py", start_path)

    if not (wsgi_files or asgi_files):
        console.print(
            "[ERROR] No 'wsgi.py' or 'asgi.py' files were found.", style="red"
        )
    return wsgi_files, closest_wsgi, asgi_files, closest_asgi


def find_settings_files(start_path: Path = Path(".")) -> list[Path]:
    """
    Search for 'settings.py' files starting from 'start_path',
    excluding any paths that contain 'site-packages'.

    :param start_path: The directory to start the search from.
    :return: A list of Path objects pointing to 'settings.py' files.
    """
    settings_files, closest_settings = find_files("*settings*.py", start_path)
    if not settings_files:
        settings_files, closest_settings = find_files("*settings/*prod*.py", start_path)
        if not settings_files:
            console.print(
                "[ERROR] No 'settings.py' files were found.", style="red"
            )
            raise typer.Abort()

    for file in settings_files:
        if file.name == "settings.py":
            return [Path(file)], file

    return settings_files, closest_settings


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
        console.print(f"[INFO] Generating {output_name}...")
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
                console.print(f"[INFO] Diff {output_name}\n")
                if existing_content == generated_lines:
                    console.print(
                        f"[INFO] Identical {output_name}\n"
                    )
                else:
                    colorize_diff(output_name, existing_content, generated_lines)
                return
            elif existing_content == generated_lines:
                console.print(f"[INFO] Identical {output_name}\n")
                return

            console.print(
                f"[WARNING] Conflict {output_name}\n",
                style="yellow bold",
            )
            colorize_diff(output_name, existing_content, generated_lines)

            if not (
                self.force
                or typer.confirm(
                    console.print("\nOverwrite?", style="yellow bold"),
                )
            ):
                console.print(f"[INFO] Skip overwriting the existing {output_name}...")
                return

        with open(output_path, "w") as f:
            f.write(generated_content)
            console.print(
                f"[INFO] Generated '{output_path}' was saved successfully!"
            )


def load_config(start_path: Path = Path(".")) -> dict:
    """
    Load the configuration from the 'pyproject.toml' file.
    :param start_path:
    :return:
    """
    _, config_path = find_files('pyproject.toml', start_path)
    if config_path:
        with config_path.open("r") as file:
            config_data = toml.load(file)
            return config_data.get('tool', {}).get('dockerfile_django', {})
    return {}


@cli.command()
def generate(
    dir: Optional[Path] = typer.Option(
        ".",
        "--dir",
        help="The directory to search for Django project files",
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=False,
        readable=True,
        resolve_path=True
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
    console.print(
        "🐳🦄✨ Welcome to Dockerfile Generator for Django projects ✨🦄🐳",
        style="magenta",
    )
    console.print(
        f"[INFO] Extracting Django project config info from '{dir}'"
    )

    config = load_config(dir)
    if config:
        console.print(
            f"[INFO] Using the configuration from 'pyproject.toml' file:"
        )
        table = Table(title="Config")
        table.add_column("Key", style="green", no_wrap=True)
        table.add_column("Value", style="green", no_wrap=True)
        for key, value in config.items():
            table.add_row(f"{key}", f"{value}")
        console.print(table)

    force = force or config.get("force", False)
    diff = diff or config.get("diff", False)
    python_version = python_version or config.get("python_version", None)

    django_project = DjangoProjectExtractor(python_version, dir)
    django_project_info = django_project.extract_project_info()
    generator = DockerfileGenerator(django_project_info, force, diff)
    generator.run()


@cli.command()
def welcome():
    """
    Display a welcome message.
    """
    console.print("🐳🦄✨ Welcome to Dockerfile Generator for Django projects ✨🦄🐳")
    console.print("Usage: dockerfile-django [COMMAND]")
    console.print("Commands:")
    console.print("  welcome         Display a welcome message")
    console.print("  generate        Generate a Dockerfile for Django projects")
    console.print(
        "Run 'dockerfile-django [COMMAND] --help' for more information on a specific command."
    )
