import argparse
import asyncio
import base64
import json
import os
import pathlib
import subprocess
import sys
import venv
from datetime import datetime
from os.path import isdir, relpath
from typing import List
from ao.ao import get_element_identifier_from_path
from ao.session import get_authenticated_session


CURRENT_FILE = pathlib.Path(__file__)
ELEMENT_PATH = CURRENT_FILE.parent.resolve()
VIRTUAL_ENVIRONMENT_PATH = ELEMENT_PATH / ".venv"
WHEELS_PATH = ELEMENT_PATH / ".wheels"

WINDOWS_OS = os.name == "nt"
PATH_TO_SCRIPTS = VIRTUAL_ENVIRONMENT_PATH / ("Scripts" if WINDOWS_OS else "bin")
PATH_TO_PIP = PATH_TO_SCRIPTS / "pip"
PATH_TO_PYTHON = PATH_TO_SCRIPTS / "python"
PATH_TO_PYTEST = PATH_TO_SCRIPTS / "pytest"
PATH_TO_PLAYWRIGHT = PATH_TO_SCRIPTS / "playwright"

EXCLUDED_FOLDERS = {
    ".venv",
    ".wheels",
    "build",
    "dist",
    "seeq_add_on_manager.egg-info",
    "tests",
}
EXCLUDED_FILES = {"element.py", "requirements.dev.txt"}
FILE_EXTENSIONS = {".py", ".txt", ".ipynb", ".json"}

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

ELEMENT_PROJECT_NAME = get_element_identifier_from_path(ELEMENT_PATH)


def bootstrap(username: str, password: str, url: str, clean: bool) -> None:
    _create_virtual_environment(clean)


def get_files_to_package() -> List[str]:
    from ao.element.add_on_tool import get_files_to_package

    return get_files_to_package(
        element_path=ELEMENT_PATH,
        file_extensions=FILE_EXTENSIONS,
        excluded_files=EXCLUDED_FILES,
        excluded_folders=EXCLUDED_FOLDERS,
    )


def watch(url: str, username: str, password: str) -> subprocess.Popen:
    # already needs to be deployed to watch -- but deployment happens through the add-on-manager now
    # deploy(url, username, password)
    from ao.element.add_on_tool import watch

    return watch(url, username, password, PATH_TO_PYTHON, CURRENT_FILE)


def test() -> None:
    from ao.element.add_on_tool import test

    return test(PATH_TO_PYTEST, ELEMENT_PATH)


async def _watch_from_environment(url: str, username: str, password: str):
    print(f"Watching {ELEMENT_PATH}")
    await asyncio.gather(hot_reload(url, username, password))


async def hot_reload(url: str, username: str, password: str):
    from ao import file_matches_criteria
    from watchfiles import awatch, Change

    requests_session, auth_header, project_id = get_authenticated_session(
        url, ELEMENT_PROJECT_NAME, username, password
    )
    async for changes in awatch(ELEMENT_PATH):
        for change in changes:
            if isdir(change[1]):
                continue  # folder creation handled in _upload_directory

            deleted = change[0] == Change.deleted
            absolute_file_path = change[1]
            destination = relpath(absolute_file_path, ELEMENT_PATH)

            if file_matches_criteria(
                str(ELEMENT_PATH),
                absolute_file_path,
                file_extensions=FILE_EXTENSIONS,
                excluded_files=EXCLUDED_FILES,
                excluded_folders=EXCLUDED_FOLDERS,
            ):
                if deleted:
                    _delete_file(
                        url,
                        requests_session,
                        auth_header,
                        project_id,
                        absolute_file_path,
                        destination,
                    )
                else:
                    _upload_file(
                        url,
                        requests_session,
                        auth_header,
                        project_id,
                        absolute_file_path,
                        destination,
                    )


def _get_jupyter_contents_api_path(url, project_id, path):
    return f"{url}/data-lab/{project_id}/api/contents/" + path.replace("\\", "//")


def _get_timestamp():
    return datetime.now().astimezone().strftime(TIMESTAMP_FORMAT)


def _upload_file(
    server_url, request_session, auth_header, project_id, source, destination
):
    from requests.exceptions import RetryError

    jupyter_path = _get_jupyter_contents_api_path(server_url, project_id, destination)
    base_name = os.path.basename(source)
    with open(source, "rb") as file:
        contents = file.read() or b""
    body = json.dumps(
        {
            "path": jupyter_path.replace("//", r"/"),
            "content": base64.b64encode(contents).decode("ascii"),
            "format": "base64",
            "name": base_name,
            "type": "file",
        }
    )
    response = None
    try:
        response = request_session.put(
            jupyter_path,
            data=body,
            headers=auth_header,
            cookies=auth_header,
            verify=True,
            timeout=60,
        )
    except RetryError:
        pass
    if response is None or response.status_code == 500:
        _upload_directory(
            server_url, auth_header, request_session, project_id, destination
        )
        try:
            response = request_session.put(
                jupyter_path,
                data=body,
                headers=auth_header,
                cookies=auth_header,
                verify=True,
                timeout=60,
            )
        except RetryError:
            pass

    status = "Success" if (response is not None) else "Failure"
    print(f"    {_get_timestamp()} Attempt to Upload {base_name} : {status}")


def _upload_directory(server_url, request_session, auth_header, project_id, full_path):
    from requests.exceptions import RetryError

    path_parts = pathlib.Path(full_path).parts
    paths_to_create = [list(path_parts[:i]) for i in range(1, len(path_parts))]
    body = json.dumps({"type": "directory"})
    base = [server_url, "data-lab", project_id, "api", "contents"]
    for path in paths_to_create:
        try:
            request_session.put(
                "/".join(base + path),
                data=body,
                headers=auth_header,
                cookies=auth_header,
                verify=True,
                timeout=60,
            )
        except RetryError:
            pass


def _delete_file(
    server_url, request_session, auth_header, project_id, source, destination
):
    from requests.exceptions import RetryError

    base_name = os.path.basename(source)
    jupyter_path = _get_jupyter_contents_api_path(server_url, project_id, destination)
    response = None
    try:
        response = request_session.delete(
            jupyter_path,
            headers=auth_header,
            cookies=auth_header,
            verify=True,
            timeout=60,
        )
    except RetryError:
        pass
    status = "Success" if (response is not None) else "Failure"
    print(f"    {_get_timestamp()} Attempt to delete {base_name} : {status}")


def _create_virtual_environment(clean: bool = False):
    if (
        not clean
        and VIRTUAL_ENVIRONMENT_PATH.exists()
        and VIRTUAL_ENVIRONMENT_PATH.is_dir()
    ):
        print("Virtual environment already exists.")
        return
    print("Creating virtual environment...")
    venv.EnvBuilder(
        system_site_packages=False, with_pip=True, clear=True, symlinks=not WINDOWS_OS
    ).create(VIRTUAL_ENVIRONMENT_PATH)
    subprocess.run(
        f"{PATH_TO_PYTHON} -m pip install --upgrade pip", shell=True, check=True
    )
    subprocess.run(
        f"{PATH_TO_PIP} install -r {ELEMENT_PATH / 'requirements.dev.txt'}"
        f" -r {ELEMENT_PATH / 'requirements.txt'}"
        f" -f {WHEELS_PATH}",
        shell=True,
        check=True,
    )
    print("Installing Playwright browsers")
    # install playwright -- needed for e2e tests
    subprocess.run(
        f"{PATH_TO_PLAYWRIGHT} install --with-deps",
        shell=True,
        check=True,
    )
    print("Virtual environment created.")


def _deploy_from_environment(url: str, username: str, password: str):
    requests_session, auth_header, project_id = get_authenticated_session(
        url, ELEMENT_PROJECT_NAME, username, password
    )
    for destination in get_files_to_package():
        source = ELEMENT_PATH / destination
        _upload_file(
            url, requests_session, auth_header, project_id, source, destination
        )


def check_dependencies() -> None:
    from ao.element.add_on_tool import check_dependencies

    return check_dependencies()


def deploy(url: str, username: str, password: str) -> None:
    # deploying is done through the add-on manager, should not be an element level function
    from ao.element.add_on_tool import deploy

    return deploy()


def get_build_dependencies() -> List[str]:
    from ao.element.add_on_tool import get_build_dependencies

    return get_build_dependencies()


def build() -> None:
    from ao.element.add_on_tool import build

    return build()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Element scripts. Must be run from the virtual environment."
    )
    parser.add_argument("--url", type=str, help="URL to the Seeq server")
    parser.add_argument("--username", type=str, help="Username for authentication")
    parser.add_argument("--password", type=str, help="Password for authentication")
    parser.add_argument(
        "--action", type=str, choices=["deploy", "watch"], help="Action to perform"
    )
    args = parser.parse_args()

    # make the add-on package available to the deploy script
    sys.path.append(os.path.abspath(os.path.join(ELEMENT_PATH, os.path.pardir)))
    if args.action == "deploy":
        if args.url is None or args.username is None or args.password is None:
            raise Exception(
                "Must provide url, username, and password arguments when deploying"
            )
        _deploy_from_environment(args.url, args.username, args.password)
    elif args.action == "watch":
        if args.url is None or args.username is None or args.password is None:
            raise Exception(
                "Must provide url, username, and password arguments when watching"
            )
        try:
            asyncio.run(_watch_from_environment(args.url, args.username, args.password))
        except KeyboardInterrupt:
            pass
