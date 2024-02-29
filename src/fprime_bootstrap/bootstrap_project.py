"""
fprime_bootstrap.bootstrap_project:

Bootstraps a new project using cookiecuter

@author thomas-bc
"""

import json
import shutil
import logging
import subprocess
import sys
from urllib.request import urlopen
from pathlib import Path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


DEFAULT_PROJECT_NAME = "MyProject"

LOGGER = logging.getLogger("fprime_bootstrap")


def bootstrap_project(parsed_args: "argparse.Namespace"):
    """Creates a new F' project"""

    # Check Python version
    if sys.version_info < (3, 8):
        LOGGER.error(
            "Python 3.8 or higher is required to use the F´ Python tooling suite. "
            "Please install Python 3.8 or higher and try again."
        )
        return 1

    # Check if Git is installed and available - needed for cloning F' as submodule
    if not shutil.which("git"):
        LOGGER.error(
            "Git is not installed or in PATH. Please install Git and try again.",
        )
        return 1

    target_dir = Path(parsed_args.path)
    # Ask user for project name
    project_name = input(f"Project name ({DEFAULT_PROJECT_NAME}): ")
    if not is_valid_name(project_name):
        return 1
    elif not project_name:
        project_name = DEFAULT_PROJECT_NAME

    project_path = target_dir / project_name

    try:
        generate_boilerplate_project(project_path, project_name)
        setup_git_repo(project_path)
        if not parsed_args.no_venv:
            setup_venv(project_path)

        print_success_message(project_name)

    except (PermissionError, FileExistsError) as out_directory_error:
        LOGGER.error(
            f"{out_directory_error}. Please select a different project name or remove the existing directory."
        )
        return 1
    except FileNotFoundError as e:
        LOGGER.error(
            f"{e}. Permission denied to write to the directory.",
        )
        return 1
    return 0


def is_valid_name(project_name: str) -> bool:
    """Checks if a project name is valid"""
    invalid_characters = [
        "#",
        "%",
        "&",
        "{",
        "}",
        "/",
        "\\",
        "<",
        ">",
        "*",
        "?",
        " ",
        "$",
        "!",
        "'",
        '"',
        ":",
        "@",
        "+",
        "`",
        "|",
        "=",
    ]
    for char in project_name:
        if char in invalid_characters:
            LOGGER.error("Invalid character in project name: {}".format(char))
            LOGGER.error("Invalid project name. ")
            return False
    return True


def setup_git_repo(project_path: Path):
    """Sets up a new git project"""
    # Retrieve latest F' release
    with urlopen("https://api.github.com/repos/nasa/fprime/releases/latest") as url:
        fprime_latest_release = json.loads(url.read().decode())
        latest_tag_name = fprime_latest_release["tag_name"]

    # Initialize git repository
    subprocess.run(["git", "init"], cwd=project_path)

    # Add F' as a submodule
    LOGGER.info(f"Checking out F´ submodule at latest release: {latest_tag_name}")
    subprocess.run(
        [
            "git",
            "submodule",
            "add",
            "--depth",
            "1",
            "https://github.com/nasa/fprime.git",
        ],
        cwd=project_path,
    )
    # Checkout F´ submodules (e.g. googletest)
    res = subprocess.run(
        ["git", "submodule", "update", "--init", "--recursive"],
        capture_output=True,
        cwd=project_path,
    )
    if res.returncode != 0:
        LOGGER.warning(
            "[WARNING] Unable to initialize submodules. Functionality may be limited."
        )

    fprime_path = project_path / "fprime"

    subprocess.run(
        ["git", "fetch", "origin", "--depth", "1", "tag", latest_tag_name],
        cwd=fprime_path,
        capture_output=True,
    )

    # Checkout requested branch/tag
    res = subprocess.run(
        ["git", "checkout", latest_tag_name],
        cwd=fprime_path,
        capture_output=True,
    )
    if res.returncode != 0:
        LOGGER.error(f"Unable to checkout tag: {latest_tag_name}. Exit...")
        sys.exit(1)


def setup_venv(project_path: Path):
    """Sets up a new virtual environment"""
    venv_path = project_path / "fprime-venv"

    LOGGER.info(f"Creating virtual environment in {venv_path} ...")
    subprocess.run([Path(sys.executable), "-m", "venv", venv_path])

    # Find pip
    pip = None
    if (venv_path / "bin/pip").exists():
        pip = venv_path / "bin/pip"
    elif (venv_path / "bin/pip3").exists():
        pip = venv_path / "bin/pip3"
    else:
        raise FileNotFoundError("Could not find pip executable in venv.")

    LOGGER.info("Upgrading pip...")
    subprocess.run([pip, "install", "--upgrade", "pip"])

    LOGGER.info("Installing F´ dependencies...")
    subprocess.run(
        [
            pip,
            "install",
            "-Ur",
            project_path / "fprime" / "requirements.txt",
        ]
    )


def generate_boilerplate_project(project_path: Path, project_name: str):
    """Generates a new project"""
    source = Path(__file__).parent / "templates/fprime-project-template"
    # copy files from template into target path
    shutil.copytree(source, project_path)

    # Iterate over all template files and replace {{FPRIME_PROJECT_NAME}} placeholder with project_name
    for file in project_path.rglob("*-template"):
        if file.is_file():
            with file.open("r") as f:
                contents = f.read()
            with file.open("w") as f:
                f.write(contents.replace(r"{{FPRIME_PROJECT_NAME}}", project_name))
            # Rename file by removing the -template suffix
            file.rename(file.parent / file.name.replace("-template", ""))


def print_success_message(project_name: str):
    """Prints a success message"""
    print(
        f"""
################################################################

Congratulations! You have successfully created a new F´ project.

A git repository has been initialized and F´ has been added as a
submodule, you can now create your first commit.

Get started with your F´ project:

-- Remember to always activate the virtual environment --
cd {project_name}
. fprime-venv/bin/activate

-- Create a new component --
fprime-util new --component

-- Create a new deployment --
fprime-util new --deployment

################################################################
"""
    )
