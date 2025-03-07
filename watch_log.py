#!/usr/bin/env python
import pathlib
import subprocess

from pick import pick
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.style import Style
from rich.theme import Theme


class LogHighlighter(RegexHighlighter):
    base_style = "log."
    highlights = [
        r"\b(?P<debug>DEBUG)\b",
        r"\b(?P<info>INFO)\b",
        r"\b(?P<warning>WARNING)\b",
        r"\b(?P<error>ERROR)\b",
        r"\b(?P<constant>(:?[0-9]+|0x[0-9a-fA-F]+|true|false|null|True|False|None))\b",
        r"\b(?P<http2xx>HTTP\/[1-2].[0-1] 2[0-9][0-9])\b",
        r"\b(?P<http3xx>HTTP\/[1-2].[0-1] 3[0-9][0-9])\b",
        r"\b(?P<http4xx>HTTP\/[1-2].[0-1] 4[0-9][0-9])\b",
        r"\b(?P<http5xx>HTTP\/[1-2].[0-1] 5[0-9][0-9])\b",
        r"\b(?P<dots>([\w-]+\.){2,}[\w-]+)\b",
        r"\b(?P<url>[a-z]+://\S+)\b",
        r"\b(?P<ipv6>([0-9a-fA-F]{2,}:){3,}(:?[0-9a-fA-F]{2,})+)\b",
        r"(?P<function>([a-zA-Z_][0-9a-zA-Z_]*\.){1,}[a-zA-Z_][0-9a-zA-Z_]*:[a-zA-Z_][0-9a-zA-Z_]*:[1-9][0-9]*)",
        r"(?P<datetime>(?P<year>[0-9]{4})-(?P<month>1[0-2]|0[1-9])-(?P<day>3[01]|0[1-9]|[12][0-9])[ T](?P<hour>2[0-3]|[01][0-9]):(?P<minute>[0-5][0-9]):(?P<second>[0-5][0-9])(?P<miliseconds>\.[0-9]{3,6})?(?P<timezone>[Z+ ][0-2][0-9]:[0-5][0-9])?)",
        r"(?<![\\\w])(?P<strings>b?[\"].*?(?<!\\)[\"])",
        r"(?<![\\\w])(?P<strings>b?[\'].*?(?<!\\)[\'])",
    ]


theme = Theme(
    {
        "log.debug": "blue",
        "log.info": "green",
        "log.warning": "yellow",
        "log.error": "red",
        "log.http2xx": "green",
        "log.http3xx": "blue",
        "log.http4xx": "yellow",
        "log.http5xx": "red",
        "log.constant": "bright_blue",
        "log.strings": "orange3",
        "log.url": Style(underline=True, color="bright_blue"),
        "log.dots": "bright_blue",
        "log.ipv6": "bright_blue",
        "log.function": "bright_blue",
        "log.datetime": "dark_green",
    }
)
console = Console(highlighter=LogHighlighter(), theme=theme)


def is_log_file(p: pathlib.Path):
    return p.is_file() and p.suffix == ".log"


log_dir = pathlib.Path("./logs")
options = [str(i) for i in log_dir.iterdir() if is_log_file(i)]

title = "Please choose the log to watch:"
file, index = pick(options, title)

process = subprocess.Popen(
    ["tail", "-F", str(file)],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)
assert process.stdout
for line in process.stdout:
    console.print(line.decode(), end="", markup=False, soft_wrap=True)
