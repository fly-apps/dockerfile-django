import difflib
import re

import typer
import secrets

from pathlib import Path


def colorize_diff(output_name: str, current_file: list, generated_file: list):
    """
    Prints a colorized diff of two sets of lines to the terminal, ignoring blank lines.

    Parameters:
    - output_name: The name of the file being compared.
    - current_file: The original lines of the file.
    - generated_file: The generated lines of the file.
    """

    diff = difflib.ndiff(
        current_file,
        generated_file,
    )

    typer.secho(f"--- Current {output_name}", fg=typer.colors.RED)
    typer.secho(f"+++ Generated {output_name}\n", fg=typer.colors.GREEN)

    for line in diff:
        # Strip the newline character from the end since `typer.secho` add it back
        stripped_line = line.rstrip("\n")
        if line.startswith("+"):
            typer.secho(stripped_line, fg=typer.colors.GREEN)
        elif line.startswith("-"):
            typer.secho(stripped_line, fg=typer.colors.RED)
        elif line.startswith("?"):
            typer.secho(stripped_line, fg=typer.colors.YELLOW)
        else:
            typer.echo(stripped_line)


def find_file_same_dir(pattern, path=".") -> Path:
    """
    Find the first file with the specified pattern in the given directory.

    Args:
        pattern (str): The pattern to search for.
        path (str, optional): The directory path to search in. Defaults to '.' (current directory).

    Returns:
        Path: The path to the found file, or None if not found.
    """
    dir_path = Path(path)
    files = list(dir_path.glob(pattern))
    if files:
        return files[0]  # Return the first file found
    else:
        return None


def find_files(pattern, start_path="."):
    """
    Find all files with the specified pattern in the given directory.

    :param pattern: The pattern to search for.
    :param start_path: The directory path to search in. Defaults to '.' (current directory).
    :return:
    """
    start_dir = Path(start_path)
    files = []

    for path in start_dir.rglob(pattern):
        if "site-packages" not in path.parts:
            files.append(path)

    return files


def check_for_keyword_in_file(file_path, keyword, skip_string_starts_with=""):
    """
    Check if a keyword is present in a file.

    :param file_path: The path to the file to check.
    :param keyword: The keyword to search for.
    :param skip_string_starts_with: Skip lines starting with this string.
    :return:
    """
    try:
        with open(file_path, "r") as file:
            for line in file:
                if line.strip().startswith(skip_string_starts_with):
                    continue
                if keyword in line:
                    return True
    except FileNotFoundError:
        pass
    return False


def get_random_secret_key(length=50) -> str:
    """
    Return a 50 character random string usable as a SECRET_KEY setting value.

    :param length: The length of the secret key.
    :return: A random secret key.
    """
    chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    return "".join(secrets.choice(chars) for i in range(length))


def extract_secret_key_from_dockerfile() -> str:
    """
    Extracts the secret key from the Dockerfile.

    :return: The secret key or an empty string if not found.
    """
    pattern = r"^ENV SECRET_KEY\s+(.*)$"

    try:
        with open("Dockerfile", "r") as file:
            for line in file:
                match = re.match(pattern, line.strip())
                if match:
                    return match.group(1)
    except FileNotFoundError:
        pass

    return ""