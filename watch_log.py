#!./venv/bin/python
import os
from pick import pick

title = "Please choose the log to watch:"
options = []

file, index = pick(options, title)
# print(index, option)

BLACK, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE = (
    r"\e[1;30m${}\e[0m",
    r"\e[1;31m${}\e[0m",
    r"\e[1;32m${}\e[0m",
    r"\e[1;33m${}\e[0m",
    r"\e[1;34m${}\e[0m",
    r"\e[1;35m${}\e[0m",
    r"\e[1;36m${}\e[0m",
    r"\e[1;37m${}\e[0m",
)


def get_cmd(file):
    log_colors = [GREEN, YELLOW, RED]
    log_matchs = [f"({level})" for level in ["INFO", "WARNING", "ERROR"]]
    http_colors = [GREEN, YELLOW, RED]
    http_matchs = [r"(HTTP\/[1-2]\.[0-2] {}[0-9][0-9])".format(i) for i in ["[2-3]", "4", "5"]]

    matchs = "|".join(log_matchs + http_matchs)
    colors = "".join([v.format(i + 1) for i, v in enumerate(log_colors + http_colors)])

    regex = f"s/{matchs}/{colors}/g"
    cmd = f"tail -F {file} | perl -pe'{regex}'"
    return cmd


cmd = get_cmd(file)
print(cmd)
os.system(cmd)