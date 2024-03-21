import argparse
import asyncio
import base64
import json
import os
import pathlib
import subprocess
import sys
import venv
import pathlib
from datetime import datetime
from os.path import isdir, relpath
from typing import List
from ao import get_add_on_identifier

CURRENT_FILE = pathlib.Path(__file__)
ELEMENT_PATH = CURRENT_FILE.parent.resolve()
VIRTUAL_ENVIRONMENT_PATH = ELEMENT_PATH / ".venv"
WHEELS_PATH = ELEMENT_PATH / ".wheels"

WINDOWS_OS = os.name == "nt"
PATH_TO_SCRIPTS = VIRTUAL_ENVIRONMENT_PATH / ("Scripts" if WINDOWS_OS else "bin")
PATH_TO_PIP = PATH_TO_SCRIPTS / "pip"
PATH_TO_PYTHON = PATH_TO_SCRIPTS / "python"
PATH_TO_PYTEST = PATH_TO_SCRIPTS / "pytest"

EXCLUDED_FOLDERS = {}
EXCLUDED_FILES = {"element.py"}
FILE_EXTENSIONS = {".json"}

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def check_dependencies() -> None:
    pass


def bootstrap(username: str, password: str, url: str, clean: bool) -> None:
    pass


def get_build_dependencies() -> List[str]:
    return []


def get_add_on_suffix():
    return os.environ.get("ADD_ON_SUFFIX", "")


def build() -> None:
    # conver the jsonnet files to json for packaging
    from build import load_jsonnet, find_files_in_folder_recursively

    jsonnet_vars = {
        "suffix": get_add_on_suffix(),
    }

    files_to_convert = find_files_in_folder_recursively(
        str(ELEMENT_PATH),
        file_extensions={".jsonnet"},
        excluded_files=EXCLUDED_FILES,
        excluded_folders=EXCLUDED_FOLDERS,
    )
    for file in files_to_convert:
        load_jsonnet(
            ELEMENT_PATH / pathlib.Path(file), tla_vars=jsonnet_vars, save=True
        )


def deploy(url: str, username: str, password: str) -> None:
    pass


def get_files_to_package() -> List[str]:
    from build import find_files_in_folder_recursively

    files_to_deploy = find_files_in_folder_recursively(
        str(ELEMENT_PATH),
        file_extensions=FILE_EXTENSIONS,
        excluded_files=EXCLUDED_FILES,
        excluded_folders=EXCLUDED_FOLDERS,
    )
    return files_to_deploy


def watch(url: str, username: str, password: str) -> subprocess.Popen:
    pass


def test() -> None:
    pass


if __name__ == "__main__":
    pass
