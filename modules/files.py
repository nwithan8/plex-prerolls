import glob
import os
from typing import List


def get_all_files_matching_glob_pattern(directory: str, pattern: str) -> List[str]:
    """
    Get all files matching a glob pattern in a directory.

    Args:
        directory (str): The directory to search in.
        pattern (str): The glob pattern to search for.

    Returns:
        List[str]: A list of file paths that match the glob pattern.
    """
    return [file for file in glob.glob(os.path.join(directory, pattern)) if os.path.isfile(file)]


def translate_local_path_to_remote_path(local_path: str, local_root_folder: str, remote_root_folder: str) -> str:
    """
    Translate a local path to a remote path.

    Args:
        local_path (str): The local path to translate.
        local_root_folder (str): The root folder of the local path.
        remote_root_folder (str): The root folder of the remote path.

    Returns:
        str: The translated remote path.
    """
    return local_path.replace(local_root_folder, remote_root_folder, 1)
