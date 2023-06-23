#!./venv/bin/python
import os
import pathlib
import shlex

from pick import pick


def is_log_file(p: pathlib.Path):
    return p.is_file() and p.suffix == ".log"


log_dir = pathlib.Path("./logs")
options = [str(i) for i in log_dir.iterdir() if is_log_file(i)]

title = "Please choose the log to watch:"
file, index = pick(options, title)


BLACK, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE = (
    r"\o033[1;30m&\o033[0m",
    r"\o033[1;31m&\o033[0m",
    r"\o033[1;32m&\o033[0m",
    r"\o033[1;33m&\o033[0m",
    r"\o033[1;34m&\o033[0m",
    r"\o033[1;35m&\o033[0m",
    r"\o033[1;36m&\o033[0m",
    r"\o033[1;37m&\o033[0m",
)
color_matchs = {
    r"INFO": GREEN,
    r"WARNING": YELLOW,
    r"ERROR": RED,
    r"DEBUG": BLUE,
    **{
        rf"HTTP\/[1-2]\.[0-1] {status}[0-9][0-9]": color
        for status, color in (
            {
                "2": GREEN,
                "3": BLUE,
                "4": YELLOW,
                "5": RED,
            }
        ).items()
    },
}


def get_cmd(file):
    cmd_tail = ["tail", "-F", file]

    cmd_sed = ["sed"]
    for k, v in color_matchs.items():
        cmd_sed.extend(["-e", f"s/{k}/{v}/g"])

    commands = [cmd_tail, cmd_sed]
    return " | ".join(shlex.join(i) for i in commands)


if __name__ == "__main__":
    cmd = get_cmd(file)
    print(cmd)
    os.system(cmd)
