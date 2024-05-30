import pathlib
import subprocess
from typing import List
from ao.utils import get_add_on_suffix


def build(element_path, excluded_files, excluded_folders) -> None:
    # conver the jsonnet files to json for packaging
    from ao.utils import load_jsonnet, find_files_in_folder_recursively

    jsonnet_vars = {
        "suffix": get_add_on_suffix(),
    }

    files_to_convert = find_files_in_folder_recursively(
        str(element_path),
        file_extensions={".jsonnet"},
        excluded_files=excluded_files,
        excluded_folders=excluded_folders,
    )
    for file in files_to_convert:
        load_jsonnet(
            element_path / pathlib.Path(file), tla_vars=jsonnet_vars, save=True
        )


def check_dependencies() -> None:
    pass


def bootstrap() -> None:
    pass


def get_build_dependencies() -> List[str]:
    return []


def deploy() -> None:
    pass


def watch() -> subprocess.Popen:
    pass


def test() -> None:
    pass
