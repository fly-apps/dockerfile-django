# Dockerfile Generator for Django Projects

This is a simple CLI that generates a Dockerfile for a Django Projects.

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

### Code Formatting

We use [Black](https://black.readthedocs.io/en/stable/) to automatically format our code according to consistent style guidelines. Black ensures that all code contributions adhere to a unified code style, promoting readability and maintainability throughout the project.

Black is already installed in the project's virtual environment.

Once installed, you can format your code using Black by running it on your project directory:

```shell
poetry run black .
```

This command will recursively format all Python files in the current directory and its subdirectories according to Black's style guidelines.

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
    