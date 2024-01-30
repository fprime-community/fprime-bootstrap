"""
fprime_bootstrap.bootstrap_project:

Bootstraps a new project using cookiecuter

@author thomas-bc
"""

import sys
from pathlib import Path
import shutil
from cookiecutter.main import cookiecutter

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def bootstrap_project(parsed_args: "argparse.Namespace"):
    """Creates a new F' project"""

    # Check if Git is installed and available - needed for cloning F' as submodule
    if not shutil.which("git"):
        print(
            "[ERROR] Git is not installed or in PATH. Please install Git and try again.",
            file=sys.stderr,
        )
        return 1

    source = (
        Path(__file__).parent / "cookiecutter_templates/cookiecutter-fprime-project"
    )
    try:
        cookiecutter(
            str(source),
            output_dir=parsed_args.path,
            extra_context={
                "__install_venv": "no" if parsed_args.no_venv else "yes",
            },
        )
    except PermissionError as out_directory_error:
        print(
            f"{out_directory_error}. Use --overwrite to overwrite (will not delete non-generated files).",
            file=sys.stderr,
        )
        return 1
    except FileNotFoundError as e:
        print(
            f"{e}. Permission denied to write to the directory.",
            file=sys.stderr,
        )
        return 1
    return 0
