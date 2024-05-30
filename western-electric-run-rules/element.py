import pathlib
import subprocess
from typing import List


CURRENT_FILE = pathlib.Path(__file__)
ELEMENT_PATH = CURRENT_FILE.parent.resolve()
EXCLUDED_FOLDERS = {}
EXCLUDED_FILES = {"element.py"}
FILE_EXTENSIONS = {".json"}


def build() -> None:
    from ao.element.formula_package import build

    return build(
        element_path=ELEMENT_PATH,
        excluded_folders=EXCLUDED_FOLDERS,
        excluded_files=EXCLUDED_FILES,
    )


def get_files_to_package() -> List[str]:
    from ao.element.formula_package import get_files_to_package

    return get_files_to_package(
        element_path=ELEMENT_PATH,
        file_extensions=FILE_EXTENSIONS,
        excluded_files=EXCLUDED_FILES,
        excluded_folders=EXCLUDED_FOLDERS,
    )


def check_dependencies() -> None:
    from ao.element.formula_package import check_dependencies

    return check_dependencies()


def bootstrap(username: str, password: str, url: str, clean: bool) -> None:
    from ao.element.formula_package import bootstrap

    return bootstrap()


def get_build_dependencies() -> List[str]:
    from ao.element.formula_package import get_build_dependencies

    return get_build_dependencies()


def deploy(url: str, username: str, password: str) -> None:
    from ao.element.formula_package import deploy

    return deploy()


def watch(url: str, username: str, password: str) -> subprocess.Popen:
    from ao.element.formula_package import watch

    return watch()


def test() -> None:
    from ao.element.formula_package import test

    return test()


if __name__ == "__main__":
    pass
