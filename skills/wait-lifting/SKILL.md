---
name: wait-lifting
description: Use PROACTIVELY before starting any stretch of autonomous work expected to take a minute or more, such as a large refactor, a multi-file migration, deep research, generating a long document, or any moment where the user will just be waiting and watching. Suggests a one-line workout, then the work starts immediately. Also use when the user asks for a "vibes check", "superset", "workout break", or "give me an exercise".
---

# Wait Lifting

Turn the user's wait time into workout time. Before starting a long stretch of autonomous work, tell the user to exercise while they wait, then start the work immediately.

## When to fire

- About to start work estimated at **1 minute or more** with no user input needed: big refactors, multi-file edits, long research, large document generation.
- The user explicitly asks for an exercise, a "vibes check", or a "superset".

## When NOT to fire

- The estimated work is under a minute.
- An exercise was already suggested in the last ~10 minutes of this conversation, by you OR by the hook. The hook fires automatically on long Bash commands and on subagent launches, so if a workout message just appeared, stay silent.
- You are about to launch a subagent (Task/Agent tool): the hook already covers that case, so don't double up.
- The user is mid-conversation and about to answer a question. Never make them exercise while you wait for THEM.

## How to dose

Scale reps to the estimated duration. Pick ONE exercise at random from this table (or the circuit for 5 min+):

| Estimated wait | Push-ups | Squats | Plank | Lunges (each leg) | Burpees |
|----------------|----------|--------|-------|-------------------|---------|
| ~1 min         | 5        | 10     | 20s   | 6                 | 3       |
| ~2 min         | 10       | 20     | 40s   | 10                | 6       |
| ~3 min         | 15       | 30     | 60s   | 15                | 9       |
| 5 min +        | Mini-circuit: 10 push-ups, 20 squats, 30s plank | | | | |

## Tone

One line, in English, with the estimated duration. Match these examples:

- "This refactor will take me about 3 minutes. 15 push-ups while you wait?"
- "About 2 min of research ahead, just enough for 20 squats."
- "I'll write the doc (~5 min), you do the circuit: 10 push-ups, 20 squats, 30s plank."

## Rules

- One line only, then start the work immediately; never wait for the user to finish exercising.
- Never block, delay, or gate the actual task on the exercise.
- If the user says stop, ignores it, or seems annoyed, drop the suggestions for the rest of the session.
