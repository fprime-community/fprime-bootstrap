# fprime-bootstrap

Easily get started on developing an F´ project with fprime-bootstrap.

More information can be found on the [F´ Installation Guide](https://nasa.github.io/fprime/getting-started.html) or at https://fprime.jpl.nasa.gov.

## Installation

Install fprime-bootstrap with:

```sh
pip install fprime-bootstrap
```

## Create a new project

Once installed, create a fresh new F´ project with:

```sh
fprime-bootstrap project
```

Options:
  - `--no-venv` : skips the creation of a [Python virtual environment](https://docs.python.org/3/library/venv.html) within the project to manage F´ tooling dependency. This is useful if you would like to use an externally-managed virtual environment. Not recommended for users who are not proficient in Python venvs.
  - `--path <PATH>` : path to create the project in. Defaults to cwd.
