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

# TODO Remove this hack
here = os.path.dirname(__file__)
sys.path.append(os.path.join(here, ".."))
from ao import get_element_identifier_from_path


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


def check_dependencies() -> None:
    pass


def bootstrap(username: str, password: str, url: str, clean: bool) -> None:
    _create_virtual_environment(clean)


def get_build_dependencies() -> List[str]:
    return []


def build() -> None:
    pass


def deploy(url: str, username: str, password: str) -> None:
    # should not be delegated to the element, should be handled by ao.py
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
    deploy(url, username, password)
    return subprocess.Popen(
        f"{PATH_TO_PYTHON} {CURRENT_FILE} --action watch"
        f" --url {url} --username {username} --password {password}",
        shell=True,
    )


def test() -> None:
    subprocess.run(f"{PATH_TO_PYTEST}", cwd=ELEMENT_PATH, check=True, shell=True)


async def _watch_from_environment(url: str, username: str, password: str):
    print(f"Watching {ELEMENT_PATH}")
    await asyncio.gather(hot_reload(url, username, password))


async def hot_reload(url: str, username: str, password: str):
    from build import file_matches_criteria
    from watchfiles import awatch, Change

    requests_session, auth_header, project_id = _get_authenticated_session(
        url, username, password
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
                # _shut_down_kernel(url, requests_session, auth_header, project_id)


def _shut_down_kernel(url: str, requests_session, auth_header, project_id):
    shut_down_endpoint = f"{url}/data-lab/{project_id}/functions/shutdown"
    requests_session.post(shut_down_endpoint, headers=auth_header, cookies=auth_header)


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
    requests_session, auth_header, project_id = _get_authenticated_session(
        url, username, password
    )
    for destination in get_files_to_package():
        source = ELEMENT_PATH / destination
        _upload_file(
            url, requests_session, auth_header, project_id, source, destination
        )


def _get_authenticated_session(url, username, password):
    from seeq import sdk, spy

    spy.login(username=username, password=password, url=url, quiet=True)
    auth_header = {"sq-auth": spy.client.auth_token}
    items_api = sdk.ItemsApi(spy.client)
    response = items_api.search_items(
        filters=[f"name=={ELEMENT_PROJECT_NAME}"], types=["Project"]
    )
    if len(response.items) == 0:
        raise Exception(f"Could not find a project with name {ELEMENT_PROJECT_NAME}")
    project_id = response.items[0].id
    requests_session = _create_requests_session()
    return requests_session, auth_header, project_id


def _create_requests_session():
    import requests
    from requests.adapters import HTTPAdapter, Retry

    max_request_retries = 5
    request_retry_status_list = [502, 503, 504]
    _http_adapter = HTTPAdapter(
        max_retries=Retry(
            total=max_request_retries,
            backoff_factor=0.5,
            status_forcelist=request_retry_status_list,
        )
    )
    request_session = requests.Session()
    request_session.mount("http://", _http_adapter)
    request_session.mount("https://", _http_adapter)
    return request_session


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
