import subprocess
from typing import runtime_checkable, Protocol, List


@runtime_checkable
class ElementProtocol(Protocol):
    def check_dependencies(self) -> None: ...
    def bootstrap(self, username: str, password: str, url: str, clean: bool) -> None: ...
    def get_build_dependencies(self) -> List[str]: ...
    def build(self) -> None: ...
    def deploy(self, username: str, password: str, url: str) -> None: ...
    def get_files_to_package(self) -> List[str]: ...
    def watch(self, url: str, username: str, password: str) -> subprocess.Popen: ...
    def test(self) -> None: ...
