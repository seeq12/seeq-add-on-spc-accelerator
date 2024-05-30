from typing import List
import subprocess


def build() -> None:
    pass


def check_dependencies() -> None:
    pass


def bootstrap() -> None:
    pass


def get_build_dependencies() -> List[str]:
    return []


def deploy() -> None:
    pass


def watch(
    url: str, username: str, password: str, path_to_python, current_file
) -> subprocess.Popen:
    return subprocess.Popen(
        f"{path_to_python} {current_file} --action watch"
        f" --url {url} --username {username} --password {password}",
        shell=True,
    )


def test(path_to_pytest, element_path) -> None:
    subprocess.run(f"{path_to_pytest}", cwd=element_path, check=True, shell=True)
