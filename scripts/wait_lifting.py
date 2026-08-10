#!/usr/bin/env python3
"""wait-lifting: turn Claude Code wait time into workout time.

PreToolUse hook on Bash and Task/Agent (subagent launches). Estimates
how long the work will take and, respecting a cooldown, prints a
systemMessage telling the user to do some exercise.

Never blocks Claude: any error -> silent exit 0, no permission decision
is ever emitted.
"""

import json
import random
import re
import sys
import time
from pathlib import Path


COOLDOWN_SECONDS = 600        # max one exercise every 10 minutes
MIN_MINUTES = 1.0             # only trigger for tasks estimated >= 1 min
SUBAGENT_MINUTES = 3.0        # flat estimate for a subagent launch
STATE_FILE = Path.home() / ".claude" / "wait-lifting.last"
MSG_FILE = Path.home() / ".claude" / "wait-lifting.msg"

# (regex, estimated minutes, short task label); first match wins
PATTERNS = [
    # --- installs ---
    (r"\b(npm|pnpm|yarn)\b[^|;&]*\b(ci|install|add)\b", 2.0, "installing deps"),
    (r"\b(pip3?|uv pip)\s+install\b", 1.5, "installing deps"),
    (r"\b(poetry|pipenv)\s+install\b|\buv\s+sync\b", 1.5, "installing deps"),
    (r"\b(bundle|composer)\s+install\b", 2.0, "installing deps"),
    (r"\b(apt|apt-get|dnf|yum|brew)\s+(-y\s+)?install\b", 2.0, "installing packages"),
    # --- builds ---
    (r"\bcargo\s+build\b.*--release", 4.0, "compiling in release mode"),
    (r"\bcargo\s+(build|check|clippy)\b", 2.0, "building"),
    (r"\bdocker(\s+compose)?\s+build\b|\bdocker-compose\s+build\b", 4.0, "building the image"),
    (r"\b(mvn|gradle|gradlew)\b[^|;&]*\b(install|build|package|assemble)\b", 3.0, "building"),
    (r"\b(npm|pnpm|yarn)\s+(run\s+)?build\b", 2.0, "building"),
    (r"\b(next|vite|nuxt|astro)\s+build\b|\bwebpack\b|\btsc\b(?!.*--watch)", 2.0, "building"),
    (r"\bgo\s+build\b|\bcmake\s+--build\b|\bmake\b(?!.*\bclean\b)", 2.0, "building"),
    (r"\bxcodebuild\b|\bflutter\s+build\b", 4.0, "building"),
    # --- tests ---
    (r"\bpytest\b|\bjest\b|\bvitest\b(?!.*--watch)|\brspec\b|\bphpunit\b", 2.0, "running tests"),
    (r"\b(npm|pnpm|yarn)\s+(run\s+)?test\b", 2.0, "running tests"),
    (r"\bgo\s+test\b|\bcargo\s+test\b|\bmvn\s+test\b|\bgradle\s+test\b", 2.0, "running tests"),
    (r"\b(playwright|cypress)\s+(test|run)\b", 3.0, "running e2e tests"),
    # --- misc long stuff ---
    (r"\bterraform\s+(plan|apply)\b|\bpulumi\s+(up|preview)\b", 3.0, "terraforming"),
    (r"\bdocker\s+pull\b|\bgit\s+clone\b", 1.5, "downloading"),
    (r"\bffmpeg\b", 2.0, "crunching media"),
    (r"\bsleep\s+(\d+)\b", None, "waiting"),  # duration = N seconds
]

# name, reps-per-minute, min, max, unit ("" = reps)
EXERCISES = [
    ("push-ups", 5, 5, 25, ""),
    ("squats", 10, 10, 40, ""),
    ("plank", 20, 20, 90, "s"),
    ("lunges (each leg)", 5, 6, 20, ""),
    ("burpees", 3, 3, 15, ""),
    ("mountain climbers", 10, 10, 40, ""),
]

CIRCUIT = "a mini-circuit (10 push-ups, 20 squats, 30s plank)"

# (info part, workout part) so displays can style them differently
TEMPLATES = [
    ("While I'm {task} (~{dur}),", "how about {ex}?"),
    ("This'll take about {dur}.", "Time for {ex} \U0001F4AA"),
    ("About {dur} of {task} ahead,", "just enough for {ex}."),
    ("I'm {task}, back in about {dur}.", "Your job: {ex}."),
    ("~{dur} of {task}.", "Squeeze in {ex}?"),
    ("Nothing to do for the next {dur}.", "Quick break: {ex}."),
]


def estimate_minutes(command):
    for pattern, minutes, label in PATTERNS:
        match = re.search(pattern, command)
        if not match:
            continue
        if minutes is None:  # sleep N
            try:
                minutes = int(match.group(1)) / 60.0
            except (ValueError, IndexError):
                minutes = 1.0
        return minutes, label
    return None, None


def cooldown_ok(now):
    try:
        last = float(STATE_FILE.read_text().strip())
        return (now - last) >= COOLDOWN_SECONDS
    except (OSError, ValueError):
        return True  # no state yet -> allowed


def save_state(now):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(str(now))
    except OSError:
        pass


def pick_exercise(minutes):
    if minutes >= 5:
        return CIRCUIT
    name, per_min, lo, hi, unit = random.choice(EXERCISES)
    amount = max(lo, min(hi, round(per_min * minutes)))
    if unit:
        article = "an" if str(amount).startswith("8") else "a"
        return "{} {}{} {}".format(article, amount, unit, name)
    return "{} {}".format(amount, name)


def fmt_duration(minutes):
    if minutes < 1:
        return "{} sec".format(int(round(minutes * 60)))
    if minutes == int(minutes):
        return "{} min".format(int(minutes))
    return "{:.0f} min".format(round(minutes))


def save_message(info, workout, minutes, now):
    try:
        MSG_FILE.write_text(json.dumps(
            {"info": info, "workout": workout, "expires": now + minutes * 60}
        ))
    except OSError:
        pass


def main():
    payload = json.load(sys.stdin)
    tool_name = payload.get("tool_name")

    if tool_name == "Bash":
        command = (payload.get("tool_input") or {}).get("command") or ""
        if not isinstance(command, str) or not command:
            return
        minutes, label = estimate_minutes(command)
    elif tool_name in ("Task", "Agent"):
        minutes, label = SUBAGENT_MINUTES, "digging into this"
    else:
        return

    if minutes is None or minutes < MIN_MINUTES:
        return

    now = time.time()
    if not cooldown_ok(now):
        return
    save_state(now)

    parts = {"dur": fmt_duration(minutes), "task": label, "ex": pick_exercise(minutes)}
    info_t, workout_t = random.choice(TEMPLATES)
    info, workout = info_t.format(**parts), workout_t.format(**parts)
    print(json.dumps({"systemMessage": info + " " + workout}))
    save_message(info, workout, minutes, now)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # never block Claude because of a workout
    sys.exit(0)
