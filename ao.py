import argparse
import glob
import importlib
import os
import pathlib
import subprocess
import sys
import zipfile
import base64
import json
from typing import Optional, List
import venv


from build import (
    load_json,
    save_json,
    topological_sort,
    ElementProtocol,
    generate_schema_default_dict,
)

PROJECT_PATH = pathlib.Path(__file__).parent.resolve()
WHEELS_PATH = PROJECT_PATH / ".wheels"
ADDON_JSON_FILE = PROJECT_PATH / "addon.json"
ADDON_JSONNET_FILE = PROJECT_PATH / "addon.jsonnet"
BOOTSTRAP_JSON_FILE = PROJECT_PATH / ".bootstrap.json"

WINDOWS_OS = os.name == "nt"
BUILD_PATH = PROJECT_PATH / "build"
E2E_TEST_PATH = PROJECT_PATH / "tests"
VIRTUAL_ENVIRONMENT_PATH = BUILD_PATH / ".venv"
PATH_TO_SCRIPTS = VIRTUAL_ENVIRONMENT_PATH / ("Scripts" if WINDOWS_OS else "bin")
PATH_TO_PIP = PATH_TO_SCRIPTS / "pip"
PATH_TO_PYTHON = PATH_TO_SCRIPTS / "python"
PATH_TO_PYTEST = PATH_TO_SCRIPTS / "pytest"
PATH_TO_PLAYWRIGHT = PATH_TO_SCRIPTS / "playwright"


ELEMENT_ACTION_FILE = "element"

IDENTIFIER = "identifier"
VERSION = "version"
ELEMENTS = "elements"
PREVIEWS = "previews"
ELEMENT_PATH = "path"
ELEMENT_IDENTIFIER = "identifier"
CONFIGURATION_SCHEMA = "configuration_schema"
ARTIFACTORY_DIR = "artifactory_dir"

DIST_FOLDER = PROJECT_PATH / "dist"
ADD_ON_EXTENSION = ".addon"
ADD_ON_METADATA_EXTENSION = ".addonmeta"

ADD_ON_MANAGER_PROJECT_NAME = "com.seeq.add-on-manager"


def get_files_to_package() -> List[str]:
    add_on_json = get_add_on_json()
    preview_files = add_on_json.get(PREVIEWS, [])
    return ["addon.json"] + preview_files


def create_package_filename(dist_base_filename: str, version: str) -> str:
    return f"{dist_base_filename}-{version}"


def get_add_on_json() -> Optional[dict]:
    from build import load_jsonnet

    jsonnet_vars = {
        "suffix": get_add_on_suffix(),
    }
    add_on_json = load_jsonnet(ADDON_JSONNET_FILE, tla_vars=jsonnet_vars, save=True)
    if add_on_json is None:
        raise Exception(f"{ADDON_JSONNET_FILE} file not found.")
    return add_on_json


def get_bootstrap_json() -> Optional[dict]:
    return load_json(BOOTSTRAP_JSON_FILE)


def get_element_paths() -> List[str]:
    add_on_json = get_add_on_json()
    if add_on_json is None or ELEMENTS not in add_on_json:
        return []
    element_paths = [element.get(ELEMENT_PATH) for element in add_on_json.get(ELEMENTS)]
    for element_path in element_paths:
        if not pathlib.Path(element_path).exists():
            raise Exception(f"Element path does not exist: {element_path}")
    return element_paths


def get_add_on_suffix():
    return os.environ.get("ADD_ON_SUFFIX", "")


def get_add_on_identifier() -> str:
    add_on_json = get_add_on_json()
    return add_on_json[IDENTIFIER]


def get_artifactory_dir() -> str:
    add_on_json = get_add_on_json()
    return add_on_json[ARTIFACTORY_DIR]


def get_add_on_package_name() -> str:
    add_on_json = get_add_on_json()
    return f"{create_package_filename(add_on_json[IDENTIFIER], add_on_json[VERSION])}"


def get_add_on_manager_api_url(project_id: str) -> str:
    bootstrap_json = get_bootstrap_json()
    base_url = bootstrap_json["url"]
    return f"{base_url}/data-lab/{project_id}/functions/notebooks/addonmanagerAPI/endpoints/add-ons"


def get_artifactory_path():
    from artifactory import ArtifactoryPath
    from urllib.parse import urljoin

    token = os.getenv("ARTIFACTORY_TOKEN")
    base_url = os.getenv("ARTIFACTORY_BASE_URL")
    artifactory_dir = get_artifactory_dir()
    artifactory_path = urljoin(base_url, artifactory_dir)
    if not all([token, base_url]):
        raise Exception(
            "Please set ARTIFACTORY_TOKEN and ARTIFACTORY_BASE_URL environment variables"
        )
    return ArtifactoryPath(artifactory_path, token=token)


def get_configuration():
    """
    Fetch the configuration of the add-on, used when deploying the add-on to add-on-manager.
    If a configuration.json file is present in an element, it will use that instead of the default configuration.
    """
    addon_json = get_add_on_json()
    config = {}
    for element in addon_json[ELEMENTS]:
        # check if there's a configuration.json file in each element. If yes, use that instead of default
        configuration_file_path = (
            pathlib.Path(element[ELEMENT_PATH]) / "configuration.json"
        )
        if configuration_file_path.exists():
            print(f"Using configuration.json for element {element[ELEMENT_IDENTIFIER]}")
            with open(configuration_file_path, "r") as f:
                config[element[ELEMENT_IDENTIFIER]] = json.load(f)
        elif "configuration_schema" in element:
            print(
                f"Using default configuration for element {element[ELEMENT_IDENTIFIER]}"
            )
            default_config = generate_schema_default_dict(element[CONFIGURATION_SCHEMA])
            config[element[ELEMENT_IDENTIFIER]] = default_config
        else:
            print(
                f"No configuration schema found for element {element[ELEMENT_IDENTIFIER]}"
            )
            pass
    return config


def get_element_identifier_from_path(element_path: pathlib.Path) -> str:
    "Used from inside an element to get its identifier from addon.json"
    add_on_json = get_add_on_json()
    elements = add_on_json[ELEMENTS]
    return next(
        element[IDENTIFIER]
        for element in elements
        if (PROJECT_PATH / element[ELEMENT_PATH]).resolve() == element_path.resolve()
    )


def get_element_config_from_identifier(element_identifier: str):
    add_on_json = get_add_on_json()
    elements = add_on_json[ELEMENTS]
    return next(
        element
        for element in elements
        if element[ELEMENT_IDENTIFIER] == element_identifier
    )


def filter_element_paths(
    element_paths: Optional[List[str]], subset_folders: Optional[List[str]]
):
    if subset_folders is None:
        return element_paths
    return [
        element_path for element_path in element_paths if element_path in subset_folders
    ]


def get_module(element_path: str) -> ElementProtocol:
    module_path = f"{element_path}.{ELEMENT_ACTION_FILE}"
    if module_path in sys.modules:
        module = sys.modules[module_path]
    else:
        module = importlib.import_module(module_path)
        assert isinstance(module, ElementProtocol)
    return module


def check_dependencies(element_paths: List[str]):
    python_version = sys.version_info
    if python_version < (3, 8):
        raise Exception("Python 3.8 or higher is required.")
    print(
        f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}"
    )
    for element_path in element_paths:
        get_module(element_path).check_dependencies()


def get_folders_from_args(args) -> Optional[List[str]]:
    if args is None or args.dir is None:
        return None
    for folder in args.dir:
        if not (PROJECT_PATH / pathlib.Path(folder)).exists():
            raise Exception(f"Folder does not exist: {folder}")
    return [str(pathlib.Path(folder)) for folder in args.dir]


def bootstrap(args):
    save_json(
        BOOTSTRAP_JSON_FILE,
        {"username": args.username, "password": args.password, "url": args.url},
    )
    # create the virtual build environment
    _create_virtual_environment(args.clean)
    # Determine the path to the site-packages directory in the virtual environment
    if WINDOWS_OS:
        site_packages_path = VIRTUAL_ENVIRONMENT_PATH / "Lib" / "site-packages"
    else:
        site_packages_path = (
            VIRTUAL_ENVIRONMENT_PATH
            / "lib"
            / f"python{sys.version_info.major}.{sys.version_info.minor}"
            / "site-packages"
        )

    sys.path.append(str(site_packages_path))
    # install playwright -- needed for e2e tests
    subprocess.run(
        f"{PATH_TO_PLAYWRIGHT} install --with-deps",
        shell=True,
        check=True,
    )
    # now go bootstrap the elements
    target_elements = filter_element_paths(
        get_element_paths(), get_folders_from_args(args)
    )
    check_dependencies(target_elements)
    for element_path in target_elements:
        print(f"Bootstrapping element: {element_path}")
        get_module(element_path).bootstrap(
            args.username, args.password, args.url, args.clean
        )


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
        f"{PATH_TO_PIP} install -r {BUILD_PATH / 'requirements.dev.txt'}"
        f" -f {WHEELS_PATH}",
        shell=True,
        check=True,
    )
    print("Virtual environment created.")


def build(args=None):
    target_elements = filter_element_paths(
        get_element_paths(), get_folders_from_args(args)
    )
    build_dependencies = {
        element_path: get_module(element_path).get_build_dependencies()
        for element_path in target_elements
    }
    sorted_elements = topological_sort(build_dependencies)
    for element_path in sorted_elements:
        print(f"Building element: {element_path}")
        get_module(element_path).build()


def uninstall(args):
    from build.add_on import AddOnManagerSession

    url, username, password = _parse_url_username_password(args)
    add_on_identifier = get_add_on_identifier()
    session = AddOnManagerSession(url, username, password)
    print("Checking if Add-on is installed")
    add_on_response = session.get_add_on(add_on_identifier)
    if add_on_response.json().get("add_on_status") == "CanUninstall":
        print("Uninstalling add-on")
        uninstall_response = session.uninstall_add_on(add_on_identifier, force=False)
        if not uninstall_response.ok:
            if (
                uninstall_response.json()["error"]["message"]
                == f"No installed Add-on found with identifier {get_add_on_identifier()}"
            ):
                raise Exception("Add-on not installed or is unable to be uninstalled")
            else:
                uninstall_response.text
                uninstall_response.raise_for_status()
    print("Uninstall complete")


def deploy(args):
    "Package and deploy the add-on to the server; assumes AoM is installed"
    from build.add_on import AddOnManagerSession

    url, username, password = _parse_url_username_password(args)
    add_on_identifier = get_add_on_identifier()
    session = AddOnManagerSession(url, username, password)

    package(args)
    # if clean, uninstall the add-on via AoM
    # TODO: allow force uninstall flag
    if args.clean:
        uninstall(args)

    # upload the add-on
    print("Uploading add-on")
    filename = f"{get_add_on_package_name()}{ADD_ON_EXTENSION}"
    with open(
        DIST_FOLDER / f"{filename}",
        "rb",
    ) as f:
        # file must be base64 encoded
        encoded_file = base64.b64encode(f.read())
        upload_response = session.upload_add_on(filename, encoded_file)
    upload_response.raise_for_status()
    print("Add-on uploaded")
    upload_response_body = upload_response.json()
    print(f"Add-on status is: {upload_response_body['add_on_status']}")

    print("Fetching configuration")
    configuration = get_configuration()
    print("Installing Add-on")
    install_response = session.install_add_on(
        add_on_identifier, upload_response_body["binary_filename"], configuration
    )
    if not install_response.ok:
        error = install_response.json()["error"]
        error_message = error["message"]
        raise Exception(f"Error installing Add-on: {error_message}")
    install_response.raise_for_status()
    print("Deployment to Add On Manager Complete")


def publish(args):
    identifier = get_add_on_identifier()
    path = get_artifactory_path()

    package(args)

    file_name = get_add_on_package_name()
    artifact_file_name = DIST_FOLDER / f"{file_name}{ADD_ON_EXTENSION}"
    metadata_file_name = DIST_FOLDER / f"{file_name}{ADD_ON_METADATA_EXTENSION}"
    files_to_upload = [artifact_file_name, metadata_file_name]

    # check that the addon and addonmeta files are there
    if not all([artifact_file_name.exists(), metadata_file_name.exists()]):
        raise Exception("Add-on package or metadata file not found")

    # delete the old artifacts, only one can exist with same identifier
    unpublish(args, path)

    if not path.exists():
        print("Creating directory...")
        path.mkdir()

    for file in files_to_upload:
        print(f"Uploading {file}")
        path.deploy_file(file)
        (path / file.name).properties = {"identifier": identifier}

    print("Done distributing")


def unpublish(args, artifactory_path=None):
    if artifactory_path is None:
        artifactory_path = get_artifactory_path()

    if not artifactory_path.exists():
        print("Nothing to unpublish")
        return

    # delete the old artifacts in that directory
    for file in artifactory_path:
        print(f"Deleting {file} in Artifactory")
        file.unlink()

    # then delete the directory
    print(f"Deleting {artifactory_path.name} in Artifactory")
    artifactory_path.unlink()

    print("Done unpublishing")


def package(args=None):
    print("Packaging")
    if not args.skip_build:
        build()
    file_name = get_add_on_package_name()

    if DIST_FOLDER.exists():
        for file in glob.glob(f"{DIST_FOLDER}/*"):
            os.remove(file)
    else:
        os.makedirs(DIST_FOLDER)

    artifact_file_name = DIST_FOLDER / f"{file_name}{ADD_ON_EXTENSION}"
    metadata_file_name = DIST_FOLDER / f"{file_name}{ADD_ON_METADATA_EXTENSION}"

    with zipfile.ZipFile(
        artifact_file_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as add_on_file:
        for filename in get_files_to_package():
            add_on_file.write(filename, filename)
        for element_path in get_element_paths():
            for filename in get_module(element_path).get_files_to_package():
                full_path = PROJECT_PATH / element_path / filename
                archive_path = pathlib.Path(element_path) / filename
                add_on_file.write(full_path, archive_path)

    with zipfile.ZipFile(
        metadata_file_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as metadata_file:
        for filename in get_files_to_package():
            metadata_file.write(filename, filename)

    print("Done packaging")


def watch(args):
    url, username, password = _parse_url_username_password(args)
    target_elements = filter_element_paths(
        get_element_paths(), get_folders_from_args(args)
    )
    processes = {}
    for element_path in target_elements:
        print(f"watching element: {element_path}")
        processes[element_path] = get_module(element_path).watch(
            url, username, password
        )
    while True:
        try:
            for process in processes.values():
                process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        except KeyboardInterrupt:
            print("Stopping watch")
            for process in processes.values():
                process.terminate()
            break


def elements_test(args):
    target_elements = filter_element_paths(
        get_element_paths(), get_folders_from_args(args)
    )
    for element_path in target_elements:
        print(f"testing element: {element_path}")
        get_module(element_path).test()
    # run E2E test if dir arg isn't passed
    if not get_folders_from_args(args):
        print("testing end-to-end")
        subprocess.run(
            f"{PATH_TO_PYTEST} -v -s",
            cwd=E2E_TEST_PATH,
            check=True,
            shell=True,
        )


def _parse_url_username_password(args=None):
    bootstrap_json = None
    if (
        args is None
        or args.username is None
        or args.password is None
        or args.url is None
    ):
        bootstrap_json = get_bootstrap_json()
        if bootstrap_json is None:
            raise Exception("Please run the bootstrap command.")
    url = args.url if hasattr(args, "url") else bootstrap_json.get("url")
    username = (
        args.username if hasattr(args, "username") else bootstrap_json.get("username")
    )
    password = (
        args.password if hasattr(args, "password") else bootstrap_json.get("password")
    )
    return url, username, password


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="ao.py", description="Add-on Manager")

    parser.add_argument("--suffix", type=str)
    subparsers = parser.add_subparsers(help="sub-command help", required=True)

    parser_bootstrap = subparsers.add_parser(
        "bootstrap", help="Bootstrap your add-on development environment"
    )
    parser_bootstrap.add_argument("--username", type=str, required=True)
    parser_bootstrap.add_argument("--password", type=str, required=True)
    parser_bootstrap.add_argument("--url", type=str, required=True)
    parser_bootstrap.add_argument(
        "--clean", action="store_true", default=False, help="Clean bootstrap"
    )
    parser_bootstrap.add_argument(
        "--dir",
        type=str,
        nargs="*",
        default=None,
        help="Execute the command for the subset of the element directories specified.",
    )
    parser_bootstrap.set_defaults(func=bootstrap)

    parser_build = subparsers.add_parser("build", help="Build your add-on")
    parser_build.add_argument(
        "--dir",
        type=str,
        nargs="*",
        default=None,
        help="Execute the command for the subset of the element directories specified.",
    )
    parser_build.set_defaults(func=build)

    parser_deploy = subparsers.add_parser("deploy", help="Deploy your add-on")
    parser_deploy.add_argument("--username", type=str)
    parser_deploy.add_argument("--password", type=str)
    parser_deploy.add_argument("--url", type=str)
    parser_deploy.add_argument(
        "--clean", action="store_true", default=False, help="Uninstall"
    )
    parser_deploy.add_argument(
        "--replace", action="store_true", default=False, help="Replace elements"
    )
    parser_deploy.add_argument(
        "--skip-build", action="store_true", default=False, help="Skip build step"
    )
    parser_deploy.set_defaults(func=deploy)

    parser_package = subparsers.add_parser("package", help="Package your add-on")
    parser_package.add_argument(
        "--skip-build", action="store_true", default=False, help="Skip build step"
    )
    parser_package.set_defaults(func=package)

    parser_watch = subparsers.add_parser(
        "watch",
        help="Build, watch, and live-update all or individual elements "
        "whenever code in the elements changes",
    )
    parser_watch.add_argument("--username", type=str)
    parser_watch.add_argument("--password", type=str)
    parser_watch.add_argument("--url", type=str)
    parser_watch.add_argument(
        "--dir",
        type=str,
        nargs="*",
        default=None,
        help="Execute the command for the subset of the element directories specified.",
    )
    parser_watch.set_defaults(func=watch)

    parser_test = subparsers.add_parser(
        "test", help="Run the tests for all or individual elements"
    )
    parser_test.add_argument(
        "--dir",
        type=str,
        nargs="*",
        default=None,
        help="Execute the command for the subset of the element directories specified.",
    )
    parser_test.set_defaults(func=elements_test)

    parser_uninstall = subparsers.add_parser(
        "uninstall", help="Uninstall the add-on from the Add-on Manager"
    )
    parser_uninstall.add_argument("--username", type=str)
    parser_uninstall.add_argument("--password", type=str)
    parser_uninstall.add_argument("--url", type=str)
    parser_uninstall.set_defaults(func=uninstall)

    parser_publish = subparsers.add_parser(
        "publish", help="distribute add-on to artifactory"
    )
    parser_publish.add_argument(
        "--skip-build", action="store_true", default=False, help="Skip build step"
    )
    parser_publish.set_defaults(func=publish)

    parser_unpublish = subparsers.add_parser(
        "unpublish", help="distribute add-on to artifactory"
    )

    parser_unpublish.set_defaults(func=unpublish)

    options, unknown = parser.parse_known_args()
    if hasattr(options, "suffix") and options.suffix is not None:
        os.environ["ADD_ON_SUFFIX"] = options.suffix

    options.func(options)
