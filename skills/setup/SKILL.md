---
name: setup
description: Configure the wait-lifting statusline so workout messages show up inside Claude Code. Use when the user runs /wait-lifting:setup or asks to set up, install, or enable the wait-lifting statusline.
---

# Wait Lifting Setup

Wire the wait-lifting statusline into the user's `~/.claude/settings.json` so workout messages appear under the input box.

## Steps

1. Read `~/.claude/settings.json` (create it with `{}` if missing).
2. If a `statusLine` key already exists and does not point to wait-lifting, show it to the user and ask before replacing it. Otherwise continue.
3. Add this key, keeping everything else untouched:

```json
"statusLine": {
  "type": "command",
  "command": "python3 \"$HOME/.claude/plugins/marketplaces/wait-lifting/scripts/statusline.py\""
}
```

4. Validate the file is still valid JSON.
5. Tell the user it takes effect on the next session restart, and that the statusline shows the coach during long tasks and a dim `model | directory` line the rest of the time.
