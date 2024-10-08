import json
import os
import pathlib
import stat
from typing import Optional, Dict, List, Set


def load_json(path: pathlib.Path) -> Optional[dict]:
    if not path.exists():
        return None
    with open(path, mode="r", encoding="utf-8") as json_file:
        return json.load(json_file)


def load_jsonnet(path: pathlib.Path, tla_vars=None, save=False) -> Optional[dict]:
    from _jsonnet import evaluate_file

    if not path.exists():
        return None
    evaluated_jsonnet = json.loads(evaluate_file(path.as_posix(), tla_vars=tla_vars))
    if save:
        save_json(path.with_suffix(".json"), evaluated_jsonnet)
    return evaluated_jsonnet


def save_json(path: pathlib.Path, values: dict) -> None:
    with open(path, mode="w", encoding="utf-8") as json_file:
        json.dump(values, json_file, indent=2, ensure_ascii=False)


def get_non_none_attr(obj, attr, default):
    value = getattr(obj, attr, default)
    return value if value is not None else default


def topological_sort(graph: Dict[str, List[str]]) -> List[str]:
    """
    Topological sort algorithm.
    :param graph: a dictionary of nodes and their dependencies
    :return: a list of nodes in topological order
    """
    result = []
    visited = set()

    def dfs(graph_node: str):
        if graph_node in visited:
            return
        visited.add(graph_node)
        for dependency in graph.get(graph_node, []):
            dfs(dependency)
        result.append(graph_node)

    for node in graph:
        dfs(node)
    return result


def find_files_in_folder_recursively(
    root: str,
    excluded_files: Set[str] = None,
    excluded_folders: Set[str] = None,
    file_extensions: Set[str] = None,
    exclude_dot_files: bool = False,
    exclude_hidden_files: bool = True,
):
    if excluded_folders is None:
        excluded_folders = {}
    files_to_deploy = list()
    for dir_path, _, files in os.walk(root):
        relative_dir_path = os.path.relpath(dir_path, root)
        if any(
            relative_dir_path.startswith(excluded_folder)
            for excluded_folder in excluded_folders
        ):
            continue
        for filename in files:
            if exclude_dot_files and filename.startswith("."):
                continue
            if (
                file_extensions is not None
                and pathlib.Path(filename).suffix not in file_extensions
            ):
                continue
            full_path = os.path.join(dir_path, filename)
            if exclude_hidden_files and _is_hidden_file(full_path):
                continue
            relative_path = os.path.relpath(full_path, root)
            if excluded_files is not None and relative_path in excluded_files:
                continue
            files_to_deploy.append(relative_path)
    return files_to_deploy


def file_matches_criteria(
    root: str,
    file: str,
    excluded_files: Set[str] = None,
    excluded_folders: Set[str] = None,
    file_extensions: Set[str] = None,
    exclude_dot_files: bool = False,
    exclude_hidden_files: bool = True,
):
    if excluded_folders is None:
        excluded_folders = {}
    relative_path = os.path.relpath(file, root)
    if any(
        relative_path.startswith(excluded_folder)
        for excluded_folder in excluded_folders
    ):
        return False
    if excluded_files is not None and relative_path in excluded_files:
        return False
    filename = os.path.basename(file)
    if exclude_dot_files and filename.startswith("."):
        return False
    if (
        file_extensions is not None
        and pathlib.Path(filename).suffix not in file_extensions
    ):
        return False
    if exclude_hidden_files and _is_hidden_file(file):
        return False
    return True


def _is_hidden_file(full_path):
    def is_windows():
        return os.name == "nt"

    def has_hidden_attribute(file_path):
        return is_windows() and bool(
            os.stat(file_path).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN
        )

    try:
        return os.path.basename(full_path).startswith(".") or has_hidden_attribute(
            full_path
        )
    except FileNotFoundError:
        return False


def generate_schema_default_dict(schema, path=""):
    """
    Recursively generate a valid instance dictionary from a given JSON schema
    that includes only the fields that are required or have a default value.

    :param schema: The JSON schema dictionary.
    :param path: The path to the current position in the schema (for nested objects).
    :return: A valid instance dictionary according to the schema.
    """
    if "type" not in schema:
        schema["type"] = "any"
    if schema["type"] == "object":
        obj = {}
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        for key, value in properties.items():
            if key in required_fields or "default" in value:
                # Construct the new path for nested objects
                new_path = f"{path}.{key}" if path else key
                # Recursive call for nested objects or fields with default values
                obj[key] = generate_schema_default_dict(value, path=new_path)
        return obj
    elif schema["type"] == "string":
        # Return the default value if specified, otherwise an empty string if required
        return schema.get("default", "")
    elif schema["type"] == "boolean":
        # Return the default value if specified, otherwise False if required
        return schema.get("default", False)
    elif schema["type"] == "array":
        # Return an empty list or the default value if specified
        return schema.get("default", [])
    elif schema["type"] == "number":
        # Return the default value if specified, otherwise 0 if required
        return schema.get("default", 0)
    elif schema["type"] == "integer":
        # Return the default value if specified, otherwise 0 if required
        return schema.get("default", 0)
    elif schema["type"] == "null":
        # Just return None for null types
        return None
    elif schema["type"] == "any":
        # return None for any type if no default
        return schema.get("default", None)
    else:
        # Extend with additional types as needed
        raise ValueError(f"Unsupported type in path {path}: {schema['type']}")
