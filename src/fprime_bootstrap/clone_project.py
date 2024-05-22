"""
fprime_bootstrap.bootstrap_project:

Bootstraps a new project using cookiecuter

@author thomas-bc
"""

import logging
import subprocess
from pathlib import Path
from fprime_bootstrap.common import (
    run_system_checks,
    setup_venv,
    print_success_message,
    OutDirectoryError,
    GitCloneError,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


LOGGER = logging.getLogger("fprime_bootstrap")


def clone_project(parsed_args: "argparse.Namespace"):
    """Creates a new F´ project"""

    # Runs system checks such as Python version, OS requirements etc...
    run_system_checks()

    target_dir = Path(parsed_args.path)

    try:
        project_path = clone_git_repo(target_dir, parsed_args.url, parsed_args.rename)
        if not parsed_args.no_venv:
            setup_venv(project_path, parsed_args.fprime_subpath)

        print_success_message(project_path)

    except (PermissionError, FileExistsError) as out_directory_error:
        raise OutDirectoryError(
            f"{out_directory_error}. Please select a different project name or remove the existing directory."
        )
    except FileNotFoundError as e:
        raise OutDirectoryError(
            f"{e}. Permission denied to write to the directory.",
        )
    return 0


def clone_git_repo(target_dir: Path, remote_url: str, new_name: str = None) -> Path:
    """Clone an F´ project using git. Uses new_name if provided for local project name"""

    if new_name:
        target_name = new_name
    else:
        # Extract the repository name from the remote_url
        target_name = remote_url.split("/")[-1]
        # Remove .git extension if present and patiently wait for Python3.9 for str.removesuffix()
        if target_name.endswith(".git"):
            target_name = target_name[:-4]

    # Add F´ as a submodule
    LOGGER.info(f"Cloning out F´ project in {target_dir} ...")
    run = subprocess.run(
        [
            "git",
            "clone",
            "--recurse-submodules",
            "--shallow-submodules",
            remote_url,
            target_name,
        ],
        cwd=target_dir,
    )

    if run.returncode != 0:
        raise GitCloneError(f"Failed to clone repository: {remote_url}")

    return target_dir / target_name
