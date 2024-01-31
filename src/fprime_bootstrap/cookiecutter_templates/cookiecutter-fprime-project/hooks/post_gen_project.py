"""
This script is run as a cookiecutter hook after the project is generated.

It does the following:
- Initializes a git repository
- Adds F' as a submodule
- Checks out the latest release of F'
- Upgrades pip and creates a virtual environment if requested

@author thomas-bc
"""

import subprocess
import sys
import requests
from pathlib import Path

response = requests.get("https://api.github.com/repos/nasa/fprime/releases/latest")
latest_tag_name = response.json()["tag_name"]

PRINT_VENV_WARNING = False


# Initialize git repository
subprocess.run(["git", "init"])

# Add F' as a submodule
print(f"[INFO] Checking out F' submodule at latest release: {latest_tag_name}")
subprocess.run(
    [
        "git",
        "submodule",
        "add",
        "--depth",
        "1",
        "https://github.com/nasa/fprime.git",
    ]
)
# Checkout F´ submodules (e.g. googletest)
res = subprocess.run(
    ["git", "submodule", "update", "--init", "--recursive"],
    capture_output=True,
)
if res.returncode != 0:
    print("[WARNING] Unable to initialize submodules. Functionality may be limited.")

subprocess.run(
    ["git", "fetch", "origin", "--depth", "1", "tag", latest_tag_name],
    cwd="./fprime",
    capture_output=True,
)

# Checkout requested branch/tag
res = subprocess.run(
    ["git", "checkout", latest_tag_name],
    cwd="./fprime",
    capture_output=True,
)
if res.returncode != 0:
    print(f"[ERROR] Unable to checkout tag: {latest_tag_name}. Exit...")
    sys.exit(1)  # sys.exit(1) indicates failure to cookiecutter


# Install venv if requested
if "{{cookiecutter.__install_venv}}" == "yes":
    try:
        print(f"[INFO] Creating virtual environment in {Path.cwd()}/fprime-venv ...")
        subprocess.run([Path(sys.executable), "-m", "venv", "./fprime-venv"])

        # Find pip
        pip = None
        if Path("./fprime-venv/bin/pip").exists():
            pip = Path("./fprime-venv/bin/pip")
        elif Path("./fprime-venv/bin/pip3").exists():
            pip = Path("./fprime-venv/bin/pip3")
        else:
            raise FileNotFoundError("Could not find pip executable in venv.")

        # Upgrade pip
        print("[INFO] Upgrading pip...")
        subprocess.run([pip, "install", "--upgrade", "pip"])
        # Install requirements.txt
        print("[INFO] Installing F´ dependencies...")
        subprocess.run(
            [
                pip,
                "install",
                "-Ur",
                Path("fprime") / "requirements.txt",
            ]
        )
    except Exception as e:
        # Print warning at the end to make sure the user sees it
        PRINT_VENV_WARNING = True
else:
    print(
        "[INFO] requirements.txt has not been installed because you did not request it.",
        "Install with `pip install -Ur fprime/requirements.txt`",
    )

print(
    """
################################################################

Congratulations! You have successfully created a new F´ project.

A git repository has been initialized and F´ has been added as a
submodule, you can now create your first commit.

Get started with your F´ project:

-- Remember to always activate the virtual environment --
cd {{ cookiecutter.project_name }}
. fprime-venv/bin/activate

-- Create a new component --
fprime-util new --component

-- Create a new deployment --
fprime-util new --deployment

################################################################
"""
)

if PRINT_VENV_WARNING:
    print(
        f"[WARNING] An error occurred while creating the virtual environment. "
        f"Please install the virtual environment manually. Error:\n{e}"
    )
