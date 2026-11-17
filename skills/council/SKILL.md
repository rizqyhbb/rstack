---
name: council
description: Pre-PR review by three fresh-context Claude reviewers with different lenses (correctness, scope and decisions, proof and UX), looped until they agree. Trigger when the user says "council", and from full-send and full-stop before filing the PR.
---

# Council

One model reviewing its own work in its own context is weak. tstack's council
uses three providers; here there is Claude only, so the diversity comes from
**fresh context** and **one narrow lens each**. If a second provider is ever
available in T3 Code (`orchestrator_capabilities`), use it for one seat and
keep the same lenses.

Before an audit, address outstanding PR comments, fix known issues, and run
the repo's checks. Give the council the updated implementation; do not defer
known fixes until reviews return.

## 1. Scope

```bash
git status --short
git fetch origin && git merge-base HEAD origin/<base>
git diff --stat <base>
```

Do not stash or discard anything. The change is base to working tree,
including untracked files. State the intent and what is out of scope in one
or two sentences each, taken from `.fullsend/TODO.md` when it exists. Note
which checks ran and their results. Do not send code the checks say is
broken.

## 2. The three seats

Launch all three in one message, as fresh subagents with no thread history
(Claude Code: three `Agent` calls, `subagent_type: general-purpose`,
high effort; T3 Code: `delegate_task` with `role: "review"` works too).
Each is read-only: no edits, commits, pushes, PR comments or subagents of
its own.

| Seat | Lens | Reads |
|---|---|---|
| **Correctness** | Bugs in the intended case, broken callers, mismatch with intent, data that can be lost or duplicated. | The diff and surrounding code. |
| **Scope & decisions** | Anything that widens the goal, touches code the goal does not need, adds options or guards nobody asked for, or contradicts a Decision. Also: anything the goal needs that is missing. | `.fullsend/TODO.md` first, then the diff. |
| **Proof & UX** | Does the stated proof actually cover each change? Are there changes with no proof? For UI: does the screen read right, states, empty and error cases, both themes, the repo's `DESIGN.md` rules. | The proof notes, the screenshots, `DESIGN.md`, the diff. |

Brief for every seat (fill in the brackets, keep the shape):

```
Review only. Do not edit, commit, push, comment on PRs, or start subagents.
Repo: <abs path>  Base: <sha>  Lens: <seat lens, one paragraph>
Intent: <intent>   Out of scope: <list>   Decisions: <list with dates>
Checks: <results>  Proof so far: <list>
See: git diff <base> [-- <paths>]; git status --short (read untracked files).
Read surrounding code before judging. Skip style unless it hides a bug.
Hold to the smallest change: flag code, tests or guards the intent does not need.
blocker = intended case wrong or a decision broken. should = real bug callers will hit, in intent. nit = rest.
Reply exactly:
SCORE: <n>/10
VERDICT: APPROVE or CHANGES
S1 [blocker|should|nit] <file>:<line> <claim>. Fix: <suggestion>
(stable ids across rounds: C1.., D1.., P1.. by seat)
```

Do not edit scoped files while a seat is reviewing. Do not wait idle: when
one result arrives, check its findings against the code while the others
run. Timeout, error or no reply is not approval; restart that seat with the
ledger.

## 3. Answer findings

Check each finding and its severity yourself. Another path, a rare case or a
small cost is a nit whatever label it came with.

- **Agree:** smallest fix. Prefer delete or narrow over a new lock, cache,
  helper or option. Fix the case that happened. One focused test that fails
  without the fix, only if the intent needs it.
- **Disagree:** say why, with evidence (file:line, test, output).
- **Contradicts a Decision:** decline, quote the decision and date. If you
  think the decision is wrong, that goes to the user, not into the diff.
- **Out of scope or nit:** decline in one line, list as a follow-up.

Keep a ledger: id, seat, severity, outcome (fixed / declined / disagree),
evidence. Re-run the checks and `git diff --shortstat <base>`. If the review
grew the diff for anything but a real bug, cut first. Do not agree just to
end the loop. It is your job to keep scope limited.

## 4. Next round

Start one only if budget remains and a blocker or should is still open, or
behaviour code changed since the last approval. Budget: 3 rounds; 5 only for
security, permissions, auth, data loss or state/concurrency while a blocker
stays open, or when the user asks. A round of nits only ends the loop.

Later rounds: same brief, plus the ledger (`fixed:` / `declined:` /
`disagree:` with evidence) and the diff since the last round. Tell each seat:
open ids and changed code only; mark each old id `resolved` or
`still open: <reason>`.

## 5. Stop

**Agreed:** all three APPROVE on the current diff, no blocker or should open,
no concern of your own. **Stuck:** an item stays disputed after two replies
or the budget ends. Show both sides in 2 to 3 lines each and ask the user
(`AskUserQuestion`, recommendation first). Budget end is not approval.

If the work ends in a pull request, put the results in the PR description,
above the attribution line:

```markdown
## Council review

Rounds: 2

| Seat | Round 1 | Round 2 |
| --- | --- | --- |
| Correctness | 7/10 | 9/10 |
| Scope & decisions | 8/10 | 10/10 |
| Proof & UX | 7/10 | 9/10 |
```

A seat that gives no score gets `no score`; never invent one. If the PR is
already open, edit the description, do not post a comment. With no PR, the
same table goes in the final reply.

Report: rounds, what changed because of the council, diff size before and
after, fixed and declined findings with reasons, and what stays disputed.
