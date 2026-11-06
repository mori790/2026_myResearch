"""The team rule. The same text is shown up front (advisory) or when the harness blocks a write (enforced)."""

RULE = """TEAM RULE FOR SHARED DECISIONS
Some choices affect both your file and your teammate's file (for example, how a value is represented,
or how a special case is signalled). Record each such choice in the shared decision log:
  python3 {tools}/agree.py status                         # what is open or already decided
  python3 {tools}/agree.py lookup TOPIC                   # read a committed decision
  python3 {tools}/agree.py propose TOPIC 'VALUE' --why "..."
  python3 {tools}/agree.py respond TOPIC accept           # or: respond TOPIC object --why "..."
  python3 {tools}/agree.py commit TOPIC                   # succeeds only when everyone accepted
  python3 {tools}/agree.py withdraw TOPIC                 # abort a proposal that is stuck or superseded
  python3 {tools}/agree.py leave                          # run this when you finish, so nobody waits for your vote
Do not write your deliverable file until at least one decision is committed and no proposal is still open.
After that, follow the committed decisions, even where they differ from your own habits or standards."""


def ready(topics):
    """The rule's condition: >=1 committed topic and no open proposal."""
    committed = [n for n, t in topics.items() if n and t["committed"]]
    open_ = [n for n, t in topics.items() if n and t["open"]]
    return bool(committed) and not open_, committed, open_
