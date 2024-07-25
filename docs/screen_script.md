bash
```bash
set -euo pipefail

session_name="tail"
start_cmd="tail -F logs/run.log"

if screen -list | grep -q $session_name; then
    read -p "Session already exists. Do you want to resume? (y/N): " response
    case "$response" in
    [yY])
        screen -r $session_name
        ;;
    *)
        exit 1
        ;;
    esac
else
    screen -S $session_name -d -m
    screen -S $session_name -X stuff "$start_cmd\n"
fi
```

python
```python
#!/usr/bin/env python
import re
import subprocess

session_name = "tail"
start_cmd = "tail -F logs/run.log"


# \t{pid}.{name}\t
session_pattern = re.compile(r"\t(?P<pid>[0-9]+)\.(?P<name>.*)\t")


def get_screen_pid(session_name: str):
    try:
        screen_list_output = subprocess.check_output(["screen", "-list"]).decode()
    except subprocess.CalledProcessError as e:
        if b"No Sockets found" in e.output:
            return None
        raise

    for session_line in screen_list_output.splitlines():
        match = session_pattern.search(session_line)
        if not match:
            continue
        if session_name == match.group("name"):
            pid = int(match.group("pid"))
            return pid


screen_pid = get_screen_pid(session_name)
if screen_pid is not None:
    print(f"Session {screen_pid}.{session_name} already exists. ")
    try:
        response = input("Do you want to resume? (y/N): ")
    except Exception:
        response = "N"

    if response.lower() == "y":
        # Reattach a session. If necessary detach and logout remotely first.
        subprocess.run(["screen", "-D", "-r", session_name])

else:
    # Start screen in detached mode
    subprocess.run(["screen", "-S", session_name, "-d", "-m"])
    # Stuff a string in the input buffer of a window.
    subprocess.run(["screen", "-S", session_name, "-X", "stuff", f"{start_cmd}\n"])

    screen_pid = get_screen_pid(session_name)
    assert screen_pid
    print(f"Starting new session {screen_pid}.{session_name}")
```
