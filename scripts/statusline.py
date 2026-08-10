#!/usr/bin/env python3
"""wait-lifting statusline: shows the current workout while a long task
runs, otherwise a minimal model | directory line."""

import json
import sys
import time
from pathlib import Path

MSG_FILE = Path.home() / ".claude" / "wait-lifting.msg"


def main():
    data = json.load(sys.stdin)
    try:
        msg = json.loads(MSG_FILE.read_text())
        if time.time() < msg["expires"]:
            print("\U0001F3CB️ {} \033[38;2;217;119;87m{}\033[0m".format(
                msg["info"], msg["workout"]))
            return
    except (OSError, ValueError, KeyError):
        pass
    model = (data.get("model") or {}).get("display_name") or ""
    cwd = (data.get("workspace") or {}).get("current_dir") or ""
    idle = " | ".join(p for p in (model, Path(cwd).name if cwd else "") if p)
    print("\033[2m{}\033[0m".format(idle))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("")
    sys.exit(0)
