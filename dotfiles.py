import argparse
import datetime
import json
import os
import shutil
import time
from termcolor import cprint


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
    source: str,
    destination: str,
    is_dir: bool = False,
    overwrite: bool = False,
    skip_prompt: bool = False,
):
    if overwrite:
        if is_dir:
            if os.path.exists(destination):
                if skip_prompt:
                    shutil.rmtree(destination)
                else:
                    # Warn the user and prompt
                    if (
                        prompt_user(
                            f"[{source}]: {destination} already exists, do you want to overwrite it?"
                        )
                        is False
                    ):
                        log_to_console(
                            "WARN",
                            f"[{source}]: {destination} already exists, not copying",
                        )
                        return False
                    shutil.rmtree(destination)
            shutil.copytree(source, destination)
        else:
            if os.path.exists(destination):
                if skip_prompt:
                    os.remove(destination)
                else:
                    # Warn the user and prompt
                    if (
                        prompt_user(
                            f"[{source}]: {destination} already exists, do you want to overwrite it?"
                        )
                        is False
                    ):
                        log_to_console(
                            "WARN",
                            f"[{source}]: {destination} already exists, not copying",
                        )
                        return False
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


def prompt_user(message: str):
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    response = input(f"[{now}]: [QUES]: {message} (y/n): ")
    if response.lower() == "y":
        return True
    return False


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
    if os.path.exists(update_from):
        if dotfile.is_dir:
            shutil.rmtree(update_to)
            shutil.copytree(update_from, update_to)
        else:
            shutil.copy(update_from, update_to)
    else:
        log_to_console(
            "ERROR",
            f"[{dotfile.copy_from}]: {dotfile.expanded_copy_to} does not exist",
        )


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
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Answer yes to all prompts",
    )

    args = parser.parse_args()

    locations = open("locations.json")

    data = json.load(locations)

    if args.yes:
        log_to_console(
            "WARN",
            "Skipping prompts, you have 4s to cancel..",
        )
        time.sleep(4)

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

        if not os.path.exists(file.expanded_path):
            log_to_console(
                "INFO", f"[{file.copy_from}]: Create directory {file.expanded_path}"
            )
            os.makedirs(file.expanded_path)
        else:
            log_to_console(
                "INFO",
                f"[{file.copy_from}]: Directory {file.expanded_path} already exists",
            )

        if args.dry_run:
            log_to_console(
                "INFO",
                f"[{file.copy_from}]: Dry run, skipping copy",
            )
            continue

        do_copy(
            file.copy_from,
            file.expanded_copy_to,
            is_dir=file.is_dir,
            overwrite=True,
            skip_prompt=args.yes,
        )

    locations.close()
