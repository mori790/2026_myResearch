---
name: agent-agreement
description: Use when you work alongside other agents and your output depends on a shared choice that has several valid but incompatible options (an interface, a data rule, a time slot, a term). Agree on the choice first, then make your output follow it.
---

# Agent Agreement

You are one of several agents producing separate outputs that must fit together.
Some choices are shared: if you and another agent each pick a different valid
option, the combined result breaks. Use this procedure for those choices.

All commands use `$TOOLS/agree.py`. Your identity is `$AGENT_ID`; the shared log
is `$AGREE_LOG`.

## 1. Spot a shared choice (topic)

Before producing output, list the choices your output depends on that another
agent's output also depends on, and where more than one option would be valid.
Give each a short topic name, e.g. `api.encode.signature`, `data.outlier_rule`,
`meeting.weekly_slot`.

Do NOT open a topic for things only you depend on, or for questions with one
correct answer.

## 2. Check, then propose or respond

```bash
python $TOOLS/agree.py status                 # what is open or decided?
python $TOOLS/agree.py lookup  TOPIC          # already decided? then follow it
python $TOOLS/agree.py propose TOPIC 'VALUE_JSON' --why "reason"
python $TOOLS/agree.py respond TOPIC accept   # or: object --why "reason"
python $TOOLS/agree.py commit  TOPIC          # succeeds only when all accepted
```

- If a topic is already committed, follow it. Do not propose a competing value.
- Make the value concrete enough to check (exact names, types, numbers, times).
- Object only with a reason and, if possible, a counter-proposal after the abort.
- Until a topic is committed, do not finalize any output that depends on it.
  You may explore and draft.

## 3. Produce output that follows the decision

Run `lookup TOPIC` right before writing the dependent part, especially after a
long pause or context loss. Use the committed value exactly.

## 4. Check before you finish

```bash
python $TOOLS/agree.py check TOPIC path/to/your/output
```

If the check fails, fix the output. If you truly cannot follow the decision,
announce it instead of diverging silently:

```bash
python $TOOLS/agree.py deviate TOPIC --why "what blocks you"
```

Then propose a revision (`propose` again on the same topic opens a new version).

## Rules

- Never change a committed value by editing files. Revisions go through `propose`.
- "I agree" in a chat message is not an agreement. Only `commit` in the log is.
- Keep topics few. One topic per incompatible choice.
