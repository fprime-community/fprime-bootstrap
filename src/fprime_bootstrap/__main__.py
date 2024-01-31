"""
fprime_bootstrap.__main__:

Main entry point for fprime-bootstrap

@author thomas-bc
"""

import sys
import os

import logging
import argparse

LOGGER = logging.getLogger("fprime_bootstrap")


def main():
    """Run wrapper, to point a console_script at"""

    parser = argparse.ArgumentParser(description="F Prime bootstrapping tool")
    subparsers = parser.add_subparsers(title="subcommands", dest="command")
    project_parser = subparsers.add_parser("project", help="Create a new F´ project")
    project_parser.add_argument(
        "--path",
        type=str,
        help="Path to create the project in (default: current directory)",
        default=os.getcwd(),
    )
    project_parser.add_argument(
        "--no-venv",
        action="store_true",
        help="Do not create a virtual environment in the project",
        default=False,
    )

    args = parser.parse_args()

    if args.command == "project":
        from fprime_bootstrap import bootstrap_project

        return bootstrap_project.bootstrap_project(args)

    LOGGER.error("[ERROR] No sub-command supplied")
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
