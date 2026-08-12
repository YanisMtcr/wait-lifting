#!/usr/bin/env python3
"""Tests for the wait-lifting scripts. Run: python3 tests/test_wait_lifting.py"""

import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


wl = load("wait_lifting")
sl = load("statusline")

TMP = Path(tempfile.mkdtemp())
wl.STATE_FILE = TMP / "last"
wl.MSG_FILE = sl.MSG_FILE = TMP / "msg"


def run(module, payload):
    sys.stdin = io.StringIO(json.dumps(payload))
    out = io.StringIO()
    sys.stdout = out
    module.main()
    sys.stdout = sys.__stdout__
    return out.getvalue().strip()


def reset():
    for f in (wl.STATE_FILE, wl.MSG_FILE):
        if f.exists():
            f.unlink()


# a long bash command triggers and writes the statusline message
reset()
out = run(wl, {"tool_name": "Bash", "tool_input": {"command": "pytest tests/ -v"}})
assert "systemMessage" in json.loads(out), "pytest should trigger"
saved = json.loads(wl.MSG_FILE.read_text())
assert saved["info"] and saved["workout"] and saved["expires"]

# subagent launches trigger with the flat estimate
for name in ("Task", "Agent"):
    reset()
    out = run(wl, {"tool_name": name, "tool_input": {"prompt": "x"}})
    assert out and "3 min" in json.loads(out)["systemMessage"], name

# short commands and other tools stay silent
reset()
assert run(wl, {"tool_name": "Bash", "tool_input": {"command": "ls -la"}}) == ""
assert run(wl, {"tool_name": "Read", "tool_input": {}}) == ""

# a second trigger within the cooldown stays silent
reset()
run(wl, {"tool_name": "Bash", "tool_input": {"command": "npm install"}})
assert run(wl, {"tool_name": "Bash", "tool_input": {"command": "npm install"}}) == ""

# timed exercises get an article ("a 40s plank", "an 80s plank")
wl.random.seed(0)
planks = [e for e in (wl.pick_exercise(2) for _ in range(80)) if "plank" in e]
assert planks and all(p.split()[0] in ("a", "an") for p in planks)

# the statusline shows the workout while fresh, then model | directory
reset()
run(wl, {"tool_name": "Bash", "tool_input": {"command": "npm install"}})
line = run(sl, {"model": {"display_name": "Fable"}, "workspace": {"current_dir": "/tmp/x"}})
assert "\U0001F3CB" in line, line
reset()
line = run(sl, {"model": {"display_name": "Fable"}, "workspace": {"current_dir": "/tmp/x"}})
assert "Fable" in line and "x" in line, line

print("all tests passed")
