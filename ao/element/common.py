from typing import List


def get_files_to_package(
    element_path, file_extensions, excluded_files, excluded_folders
) -> List[str]:
    from ao.utils import find_files_in_folder_recursively

    files_to_deploy = find_files_in_folder_recursively(
        str(element_path),
        file_extensions=file_extensions,
        excluded_files=excluded_files,
        excluded_folders=excluded_folders,
    )
    return files_to_deploy
