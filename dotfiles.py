import argparse
import datetime
import json
import os
import shutil
import sys
from termcolor import colored, cprint


class Dotfiles:
    def __init__(self, dotfile, data):
        self.data = data
        self.name = dotfile
        self.copy_from = data[dotfile]["copy_from"]
        self.copy_to = data[dotfile]["copy_to"]
        self.path = data[dotfile]["path"]
        self.filename = data[dotfile]["filename"]
        self.is_dir = data[dotfile]["is_dir"]

        self.expanded_path = os.path.expanduser(self.path)
        self.expanded_copy_to = os.path.expanduser(self.copy_to)


def do_copy(
    source: str, destination: str, is_dir: bool = False, overwrite: bool = False
):
    if overwrite:
        if is_dir:
            if os.path.exists(destination):
                shutil.rmtree(destination)
            shutil.copytree(source, destination)
        else:
            if os.path.exists(destination):
                os.remove(destination)
            shutil.copy(source, destination)

        log_to_console("OKAY", f"[{source}]: Copied {source} to {destination}")
        return True
    else:
        if os.path.exists(destination):
            log_to_console(
                "WARN", f"[{source}]: {destination} already exists, not copying"
            )
            return False
        else:
            if is_dir:
                shutil.copytree(source, destination)
            else:
                shutil.copy(source, destination)

            log_to_console("OKAY", f"[{source}]: Copied {source} to {destination}")
            return True


def log_to_console(level: str, message: str):
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    message = f"[{now}]: [{level}]: {message}"
    if level == "INFO":
        cprint(message, "blue")
    elif level == "OKAY":
        cprint(message, "green")
    elif level == "WARN":
        cprint(message, "yellow")
    elif level == "ERROR":
        cprint(message, "red")
    else:
        cprint(message, "white")


def do_upload(dotfile):
    update_from = dotfile.expanded_copy_to
    update_to = dotfile.copy_from
    if dotfile.is_dir:
        shutil.rmtree(update_to)
        shutil.copytree(update_from, update_to)
    else:
        shutil.copy(update_from, update_to)


def handle_dotfiles_run(expanded_copy_to, copy_to, copy_from):
    if os.path.exists(expanded_copy_to):
        with open(expanded_copy_to, "r") as run_file:
            last_run = run_file.read()
            log_to_console(
                "INFO",
                f"Last dotfiles run (according to {copy_to}) was {last_run}",
            )
            run_file.close()
        os.remove(expanded_copy_to)
    with open(copy_from, "w") as run_file:
        now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        run_file.write(now)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage dotfiles")
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Do not actually copy anything",
    )
    parser.add_argument(
        "-u",
        "--upload",
        action="store_true",
        help="Update repo with current dotfiles",
    )

    args = parser.parse_args()

    locations = open("locations.json")

    data = json.load(locations)

    for dotfile in data:
        file = Dotfiles(dotfile, data)

        if args.upload:
            log_to_console(
                "INFO",
                f"Running in upload mode, updating {file.copy_from} from {file.expanded_copy_to}",
            )
            do_upload(file)
            continue

        if file.name == "dotfiles_run":
            handle_dotfiles_run(file.expanded_copy_to, file.copy_to, file.copy_from)

        if file.path == "~":
            log_to_console(
                "INFO",
                f"[{file.copy_from}]: File path is the root the current user's home directory",
            )
        else:
            if not os.path.exists(file.expanded_path):
                log_to_console(
                    "INFO", f"[{file.copy_from}]: Create directory {file.expanded_path}"
                )
            else:
                log_to_console(
                    "INFO",
                    f"[{file.copy_from}]: Directory {file.expanded_path} already exists",
                )

        if file.name != file.filename:
            log_to_console(
                "INFO",
                f"[{file.copy_from}]: Copy to {file.copy_to} (rename to {file.filename}) ({'directory' if file.is_dir else 'file'})",
            )
        else:
            log_to_console(
                "INFO",
                f"[{file.copy_from}]: Copy to {file.copy_to} ({'directory' if file.is_dir else 'file'})",
            )

        do_copy(
            file.copy_from, file.expanded_copy_to, is_dir=file.is_dir, overwrite=False
        )

    locations.close()
