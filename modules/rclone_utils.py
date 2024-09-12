import subprocess

RCLONE_REMOTE_PATH = "RCLONE_REMOTE_PATH_PLACEHOLDER"


def _build_rclone_full_path(rclone_remote: str, rclone_path: str) -> str:
    """
    Build the full rclone path.

    :param rclone_remote: The rclone remote.
    :param rclone_path: The rclone path to the directory.
    :return: The full rclone path.
    """
    return f"{rclone_remote}:{rclone_path}"


def _add_config_path_to_args(args: list[str], rclone_config_path: str) -> list[str]:
    """
    Add the rclone config path to the arguments.

    :param args: The arguments.
    :param rclone_config_path: The rclone config path.
    :return: The arguments with the rclone config path added.
    """
    args.append(f'--config={rclone_config_path}')

    return args


def _add_rclone_remote_to_args(args: list[str], rclone_remote: str, rclone_path: str) -> list[str]:
    """
    Add the rclone remote to the arguments.

    :param args: The arguments.
    :param rclone_remote: The rclone remote.
    :param rclone_path: The rclone path to the directory.
    :return: The arguments with the rclone remote added.
    """
    rclone_full_path = _build_rclone_full_path(rclone_remote=rclone_remote, rclone_path=rclone_path)
    for i, arg in enumerate(args):
        if RCLONE_REMOTE_PATH in arg:  # Replace the placeholder with the actual rclone path
            args[i] = arg.replace(RCLONE_REMOTE_PATH, f'{rclone_full_path}')

    return args


def create_path_if_not_exists(rclone_remote: str, rclone_path: str, rclone_config_path: str):
    """
    Create a directory if it does not exist.

    :param rclone_remote: The rclone remote.
    :param rclone_path: The rclone path to the directory.
    :param rclone_config_path: The rclone config path.
    """
    run_args = ['rclone', 'mkdir', RCLONE_REMOTE_PATH]
    run_args = _add_rclone_remote_to_args(args=run_args, rclone_remote=rclone_remote, rclone_path=rclone_path)
    run_args = _add_config_path_to_args(args=run_args, rclone_config_path=rclone_config_path)
    subprocess.run(run_args)


def copy_local_file_to_remote_directory(local_file_path: str, rclone_remote: str, rclone_path: str,
                                        rclone_config_path: str):
    """
    Copy a local file to a remote directory.

    :param local_file_path: The local file path.
    :param rclone_remote: The rclone remote.
    :param rclone_path: The rclone path to the directory.
    :param rclone_config_path: The rclone config path.
    """
    create_path_if_not_exists(rclone_remote=rclone_remote, rclone_path=rclone_path,
                              rclone_config_path=rclone_config_path)
    run_args = ['rclone', 'copy', local_file_path, RCLONE_REMOTE_PATH]
    run_args = _add_rclone_remote_to_args(args=run_args, rclone_remote=rclone_remote, rclone_path=rclone_path)
    run_args = _add_config_path_to_args(args=run_args, rclone_config_path=rclone_config_path)
    subprocess.run(run_args)


def delete_remote_file(rclone_remote: str, rclone_path: str, rclone_config_path: str):
    """
    Delete a remote file.

    :param rclone_remote: The rclone remote.
    :param rclone_path: The rclone path to the directory.
    :param rclone_config_path: The rclone config path.
    """
    run_args = ['rclone', 'delete', RCLONE_REMOTE_PATH]
    run_args = _add_rclone_remote_to_args(args=run_args, rclone_remote=rclone_remote, rclone_path=rclone_path)
    run_args = _add_config_path_to_args(args=run_args, rclone_config_path=rclone_config_path)
    subprocess.run(run_args)


def get_all_files_in_directory_beyond_most_recent_x_count(rclone_remote: str, rclone_path: str, rclone_config_path: str,
                                                          count: int) -> list[str]:
    """
    Get all files in a directory beyond the most recent X count.
    NOTE: Assumes all files in the directory end with epoch timestamps that can be sorted "alphabetically".

    :param rclone_remote: The rclone remote.
    :param rclone_path: The rclone path to the directory.
    :param rclone_config_path: The rclone config path.
    :param count: The number of most recent files to keep.
    :return: A list of file paths that are beyond the most recent X count.
    """
    output_file = "file_list.txt"

    list_run_args = ['rclone', 'lsf', RCLONE_REMOTE_PATH]
    list_run_args = _add_rclone_remote_to_args(args=list_run_args, rclone_remote=rclone_remote, rclone_path=rclone_path)
    list_run_args = _add_config_path_to_args(args=list_run_args, rclone_config_path=rclone_config_path)

    sort_run_args = ['sort', '-r']
    tail_run_args = ['tail', '-n', f'+{count}']

    with open(output_file, "w") as f:
        list_process = subprocess.Popen(list_run_args, stdout=subprocess.PIPE)
        sort_process = subprocess.Popen(sort_run_args, stdin=list_process.stdout, stdout=subprocess.PIPE)
        tail_process = subprocess.Popen(tail_run_args, stdin=sort_process.stdout, stdout=f)
        tail_process.communicate()

    with open(output_file, "r") as f:
        return [line.strip() for line in f.readlines()]
