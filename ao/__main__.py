import argparse
import os
from ao import (
    bootstrap,
    build,
    deploy,
    package,
    watch,
    elements_test,
    uninstall,
    publish,
    unpublish,
)


def main():
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

    options, _ = parser.parse_known_args()
    if hasattr(options, "suffix") and options.suffix is not None:
        os.environ["ADD_ON_SUFFIX"] = options.suffix

    options.func(options)


if __name__ == "__main__":
    main()
