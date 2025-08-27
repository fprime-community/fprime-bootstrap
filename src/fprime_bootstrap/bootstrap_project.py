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
from urllib.error import HTTPError
from pathlib import Path

from fprime_bootstrap.common import (
    run_system_checks,
    print_success_message,
    setup_venv,
    OutDirectoryError,
    InvalidProjectName,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


DEFAULT_REPO_NAME = "my-fprime-project"

LOGGER = logging.getLogger("fprime_bootstrap")


def bootstrap_project(parsed_args: "argparse.Namespace"):
    """Creates a new F´ project"""

    # Runs system checks such as Python version, OS requirements etc...
    run_system_checks()
    # Run contextual checks, such as parent path and project name
    run_context_checks(parsed_args.path)

    # Retrieve latest F´ release
    if parsed_args.tag:
        tag_name = parsed_args.tag
    else:
        tag_name = get_latest_fprime_release()

    target_dir = Path(parsed_args.path)
    # Ask for repository name
    repo_name = (
        (input(f"Project repository name [{DEFAULT_REPO_NAME}]: ") or DEFAULT_REPO_NAME)
        if not parsed_args.populate
        else target_dir.name
    )
    # Ask user for project name
    default_project_name = kebab_to_pascal_case(repo_name)
    project_namespace = (
        (
            input(f"Project top-level namespace [{default_project_name}]: ")
            or default_project_name
        )
        if not parsed_args.populate
        else target_dir.name
    )
    check_project_name(project_namespace)

    project_path = target_dir / repo_name if not parsed_args.populate else target_dir

    try:
        generate_boilerplate_project(
            project_path, project_namespace, tag_name, populate=parsed_args.populate
        )
        setup_git_repo(project_path, tag_name)
        if not parsed_args.no_venv:
            setup_venv(project_path)

        print_success_message(repo_name)

    except (PermissionError, FileExistsError) as out_directory_error:
        raise OutDirectoryError(
            f"{out_directory_error}. Please select a different project name or remove the existing directory."
        )
    except FileNotFoundError as e:
        raise OutDirectoryError(
            f"{e}. Permission denied to write to the directory.",
        )
    return 0


def check_project_name(project_name: str) -> bool:
    """Checks if a project name is valid. Project name should be a valid
    FPP identifier, it should only contain alphanumeric characters and underscores."""
    if not project_name.isalnum():
        raise InvalidProjectName(
            f"Invalid project name: {project_name}. "
            "Project name should only contain alphanumeric characters and underscores."
        )


def run_context_checks(project_path: Path):
    real_path = Path(project_path).resolve()

    # Check that no ' " and spaces are in the path and its parents
    if any(char in str(real_path.name) for char in ['"', "'", "´", " "]):
        raise InvalidProjectName(
            f"Special characters such as single or double quotes and spaces are not allowed in the project path: {real_path}."
        )

    # TODO:
    # 1) Ideally we would check that the path is not a symlink here, but it doesn't seem to be doable in Python... ?
    # 2) Elegant way of dealing with line endings in Windows (see https://github.com/nasa/fprime/issues/2566)
    return 0


def setup_git_repo(project_path: Path, tag_name: str):
    """Sets up a new git project"""
    # Initialize git repository
    subprocess.run(["git", "init"], cwd=project_path)

    library_path = project_path / "lib"

    # Add F´ as a submodule
    LOGGER.info(f"Checking out F´ submodule at version: {tag_name}")
    subprocess.run(
        [
            "git",
            "submodule",
            "add",
            "--depth",
            "1",
            "https://github.com/nasa/fprime.git",
        ],
        cwd=library_path,
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

    fprime_path = library_path / "fprime"

    subprocess.run(
        ["git", "fetch", "origin", "--depth", "1", "tag", tag_name],
        cwd=fprime_path,
        capture_output=True,
    )

    # Checkout requested branch/tag
    res = subprocess.run(
        ["git", "checkout", tag_name],
        cwd=fprime_path,
        capture_output=True,
    )
    if res.returncode != 0:
        LOGGER.error(f"Unable to checkout tag: {tag_name}.")
        LOGGER.error(
            "Please set the --tag environment variable to a valid F´ release tag and try again."
        )
        sys.exit(1)

    # Initial commit
    subprocess.run(
        ["git", "commit", "-m", "Initial commit (by fprime-bootstrap)"],
        cwd=project_path,
        capture_output=True,
    )
    subprocess.run(["git", "add", "."], cwd=project_path, capture_output=True)
    res = subprocess.run(
        ["git", "commit", "-m", "Add F Prime project content (by fprime-bootstrap)"],
        cwd=project_path,
        capture_output=True,
    )
    if res.returncode != 0:
        LOGGER.warning("Unable to perform initial commit.")


def rename_template_file(file: Path, project_name: str):
    """Rename a file, removing -template and replacing {{FPRIME_PROJECT_NAME}}"""
    new_name = file.name.replace(r"{{FPRIME_PROJECT_NAME}}", project_name).replace(
        "-template", ""
    )
    if new_name != file.name:
        file.rename(file.parent / new_name)


def generate_boilerplate_project(
    project_path: Path, project_name: str, tag: str, populate: bool = False
):
    """Generates a new project"""
    source = Path(__file__).parent / "templates/fprime-project-template"
    # copy files from template into target path
    shutil.copytree(source, project_path, dirs_exist_ok=populate)

    # Iterate over all template files and replace {{FPRIME_PROJECT_NAME}} placeholder with project_name
    for file in project_path.rglob("*-template"):
        if file.is_file():
            with file.open("r") as f:
                contents = f.read()
            with file.open("w") as f:
                f.write(
                    contents.replace(r"{{FPRIME_PROJECT_NAME}}", project_name).replace(
                        "{{ TAG }}", tag
                    )
                )
            rename_template_file(file, project_name)

    # After updating all the files, update the folders
    for directory in project_path.rglob("*-template"):
        if directory.is_dir():
            rename_template_file(directory, project_name)


def get_latest_fprime_release() -> str:
    """Retrieves the latest F´ release from GitHub

    Note: Using the GitHub API is the simplest and most reliable way to get the
    latest release. However, in some cases the API may not be respond (e.g. rate
    limit exceeded). In these cases, we fall back to using `git ls-remote` to get
    the latest tag. This approach seems fragile (will the format of the output change?),
    but it's the best we can do without the API.
    """
    try:
        with urlopen("https://api.github.com/repos/nasa/fprime/releases/latest") as url:
            fprime_latest_release = json.loads(url.read().decode())
            return fprime_latest_release["tag_name"]
    except HTTPError:
        stdout = subprocess.Popen(
            [
                "git",
                "ls-remote",
                "--tags",
                "--refs",
                "https://github.com/nasa/fprime",
            ],
            stdout=subprocess.PIPE,
        ).stdout.readlines()

        import re

        # This regex only matches tags in the format v1.2.3, and NOT v1.2.3-rc1 or v1.2.3a1 etc...
        tags = re.findall(r"v\d+\.\d+\.\d+\b", "".join(map(str, stdout)))

        # Used to compare semantic versions, e.g. v3.11.0 > v3.7.0
        def version_tuple(version):
            return tuple(map(int, version.lstrip("v").split(".")))

        return max(tags, key=version_tuple)


def kebab_to_pascal_case(kebab_string):
    """Converts a kebab-case string to PascalCase.

    Args:
      kebab_string: The string in kebab-case.

    Returns:
      The string converted to PascalCase.
    """
    words = kebab_string.split("-")
    return "".join(word.capitalize() for word in words)
