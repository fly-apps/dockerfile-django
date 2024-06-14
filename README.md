# Dockerfile Generator for Django Projects

This is a simple CLI that generates a Dockerfile for a Django Projects.

## Usage

### Generate a Dockerfile

With `dockerfile-django` installed, you can generate a Dockerfile for your Django project. The command will search for the Django project files in the specified directory and generate a Dockerfile for your Django application.

Go to the root directory of your Django project and run the following command:

```shell
dockerfile-django generate
```

By default, the command will search for Django project files in the current directory.

### General Options

- `--dir`: The directory path to search for Django project files. By default, it is set to the current directory.
- `--force`: Force overwriting the existing Dockerfile. By default, it is set to `False`.
- `--diff`: Display differences between the current and generated Dockerfile. By default, it is set to `False`.
- `--pyver`: Python version to use in the Dockerfile. By default, it is set to `DEFAULT_PYTHON_VERSION` (3.12).
- `--help`: Show the help message and exit.

### Example

```shell
dockerfile-django generate --dir /.../Projects/my-djanogo-project/ --diff --pyver "3.11.4"
```

This command will search for Django project files in the `/.../Projects/my-djanogo-project/` directory (and all subdirectories) and generate a Dockerfile with Python version `3.11.4`. It will also display the differences between the current and generated Dockerfile but not force save the generated Dockerfile.

### Save Default Options

You can save default options for the `dockerfile-django` command by creating/updating a `pyproject.toml` file in your project directory.

`[tool]` table is used to store the default options for the `dockerfile-django` command.

```toml
# pyproject.toml

[tool.dockerfile_django]
dir = "...Projects/my-djanogo-project/"
force = false
diff = true
pyver = "3.11.4"
```

`dockerfile-django` will use the default options from the `pyproject.toml` file if no options are provided.

You can also override the default options by providing the [options](#general-options) in the command line.

## Contributing

### Setting up the project

> Before you can start this project, you'll need to install [Poetry](https://python-poetry.org/), a tool for dependency management and packaging in Python. 
> For full installation instructions, please refer to the [Poetry documentation](https://python-poetry.org/docs/#installation).

1. Clone the repository
2. Navigate to the project directory (root)
3. Run `poetry install` to create the virtual environment and install the dependencies
4. Run `poetry shell` to activate the virtual environment
5. Once you are done, you can deactivate the virtual environment by running `exit` or closing the terminal.

```shell
git clone https://github.com/fly-apps/dockerfile-django.git
cd dockerfile-django
poetry install
poetry shell
```

### Running the commands

To get help and see the available options for the `dockerfile-django` command, you can use the following command:

```shell
poetry run dockerfile-django --help
```

```output
 Usage: dockerfile-django [OPTIONS] COMMAND [ARGS]...                                                                                                                        
                                                                                                                                                                             
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                          │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.   │
│ --help                        Show this message and exit.                                                        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ generate   Generate a Dockerfile for Django projects.                                                            │
│ welcome    Display a welcome message.                                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### Generating a Dockerfile
```shell
poetry run dockerfile-django generate --help
```

```output
 Usage: dockerfile-django generate [OPTIONS]                                                                                   
                                                                                                                               
 Generate a Dockerfile for Django projects.                                                                                    
                                                                                                                               
╭─ Options ─────────────────────────────────────────────────────────────────────────────╮
│ --dir          TEXT  The directory to search for Django project files [default: .]    │
│ --force              Force overwriting the existing Dockerfile                        │
│ --diff               Display differences between current and generated Dockerfile     │
│ --pyver        TEXT  Python version to use in the Dockerfile [default: None]          │
│ --help               Show this message and exit.                                      │
╰───────────────────────────────────────────────────────────────────────────────────────╯
```

### Linters and Code Formatters

[Ruff](https://docs.astral.sh/ruff/) is a fast and configurable Python linter and formatter written in Rust. 

Ruff is already installed in the project's virtual environment (dev).

Once installed, you can run `ruff check` to lint the files, which mean it analyses the code to find and report issues related to style, potential errors, and best practices:

```shell
poetry run ruff check .
```

and use `--fix` option to fix any fixable errors:

```shell
poetry run ruff check . --fix
```

Additionally, you can automatically format your code to comply with the style guidelines enforced by running:

```shell
poetry run ruff format .
```

> Specific **linter** and **format** configurations are described on `pyproject.toml` on tables `[tool.ruff.lint]` and `[tool.ruff.format]`, respectively.

### Generating a Dockerfile for a Test Case

To generate a Dockerfile for a test case, you can use the following command:

```shell
poetry run dockerfile-django generate --dir tests/test_cases/server/gunicorn/ --pyver "3.12"
```

### Running Tests

To run the tests, you can follow the steps below:

#### Running the tests directly in the virtual environment

1. Navigate to the project directory (root)
2. Run the tests directly in the virtual environment

```shell
cd dockerfile-django/
poetry run pytest
```

To produce a coverage report, run:

```shell
poetry run pytest --cov=dockerfile_django
```

#### Activating the virtual environment and running the tests

1. Navigate to the project directory (root)
2. Activate the virtual environment
3. Run the tests

```shell
cd dockerfile-django/
poetry shell
pytest
```

### Capturing test results

To assist with this process, outputs of tests can be captured automatically. This is useful when adding new tests and when making a change that affects many tests. Be sure to inspect the output (e.g., by using git diff) before committing.

Capturing test results is done by setting the following environment variable before running `pytest`:

    TEST_CAPTURE=1
    