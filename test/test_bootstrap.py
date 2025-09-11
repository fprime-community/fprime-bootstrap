"""
=================================================
Filename   : test_bootstrap.py
Author     : rmzmrnn
Created    : 2025-06-19
Description: pytest script for fprime-bootstrap
=================================================
"""

import subprocess
import sys
import os
import pytest
import shutil
from pathlib import Path

DEFAULT_PROJECT_NAME = "MyProject"
TMP_FOLDER = "tmp"
TEMPLATE_FOLDER = "src/fprime_bootstrap/templates/fprime-project-template"
GIT_REPOSITORY = "https://github.com/fprime-community/fprime-workshop-led-blinker"


@pytest.fixture(scope="session", autouse=True)
def cleanup_tmp():
    """
    Fixture to clean up the tmp directory after all tests complete
    """
    yield  # This allows tests to run first
    # Cleanup after all tests in the session
    if os.path.exists(TMP_FOLDER):
        shutil.rmtree(TMP_FOLDER)


@pytest.fixture
def setup_tmp_folder():
    """
    Fixture to ensure tmp folder exists for each test
    """
    if not os.path.exists(TMP_FOLDER):
        os.mkdir(TMP_FOLDER)
    yield TMP_FOLDER


@pytest.mark.bootstrap
@pytest.mark.project
def test_bootstrap_project(setup_tmp_folder):
    """
    Tests if bootstrap project works properly
    """

    project_folder = os.path.join(TMP_FOLDER, DEFAULT_PROJECT_NAME)
    if os.path.exists(project_folder):
        shutil.rmtree(project_folder)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fprime_bootstrap",
            "project",
            "--path",
            os.path.join("..", TMP_FOLDER),
            "--no-venv",
        ],
        cwd="src",
        capture_output=True,
        input=DEFAULT_PROJECT_NAME + "\n" + DEFAULT_PROJECT_NAME + "\n",
        text=True,
    )

    assert result.returncode == 0


@pytest.mark.bootstrap
@pytest.mark.template
def test_no_template_files():
    """
    Tests if bootstrap project does not have *-template files
    """

    project_folder = Path(TMP_FOLDER, DEFAULT_PROJECT_NAME)
    assert os.path.exists(project_folder)

    template_files_list = [
        "\t" + str(file) for file in project_folder.rglob("*-template")
    ]

    if template_files_list:
        pytest.fail("\n" + "\n".join(template_files_list))


@pytest.mark.bootstrap
@pytest.mark.replace
def test_fprime_project_name_replace():
    """
    Tests if {{FPRIME_PROJECT_NAME}} has been replaced with the project name.
    """

    project_folder = Path(TMP_FOLDER, DEFAULT_PROJECT_NAME)
    assert os.path.exists(project_folder)

    if list(project_folder.rglob("*-template")):
        pytest.fail("*-template files are not properly renamed")

    template_folder = Path(TEMPLATE_FOLDER)
    project_files = [
        project_folder
        / file.relative_to(template_folder).with_name(
            file.name.replace("-template", "")
        )
        for file in template_folder.rglob("*-template")
    ]

    files_dict = {}
    error_strings = []

    for file in project_files:
        if file.is_file():
            with file.open("r") as f:
                contents = f.readlines()
                lines = []

                for index in range(len(contents)):
                    if contents[index].find(r"{{FPRIME_PROJECT_NAME}}") != -1:
                        lines.append(
                            "\tLine {}: {}".format(
                                index + 1, contents[index].replace("\n", "")
                            )
                        )

                if lines:
                    files_dict.update({str(file): lines})

    for file_path, value in files_dict.items():
        error_strings.append("{}\n{}".format(file_path, "\n".join(value)))

    if files_dict:
        pytest.fail("\n" + "\n".join(error_strings))


@pytest.mark.clone
def test_bootstrap_clone(setup_tmp_folder):
    """
    Tests if bootstrap clone works properly
    """

    git_folder_name = GIT_REPOSITORY.split("/")[-1]
    git_project_folder = os.path.join(TMP_FOLDER, git_folder_name)
    if os.path.exists(git_project_folder):
        shutil.rmtree(git_project_folder)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fprime_bootstrap",
            "clone",
            GIT_REPOSITORY,
            "--path",
            os.path.join("..", TMP_FOLDER),
            "--no-venv",
        ],
        cwd="src",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
