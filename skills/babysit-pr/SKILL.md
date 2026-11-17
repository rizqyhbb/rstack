---
name: babysit-pr
description: Monitor a pull request through review bots and checks until its merge gate passes, fixing real findings without widening the PR. Use when the user asks to monitor, watch, or babysit a PR, and from full-send and full-stop.
---

# Babysit PR

Take a PR from "filed" to "merge gate passes" without growing it, without
reversing decisions, and without a human watching. This skill never merges
on its own; `full-send` does that after the gate.

## 0. Read the contract

If `.fullsend/TODO.md` exists in the worktree, read it before the first
review: **Goal**, **Out of scope**, **Decisions** (with dates), **Review**
(mode and reviewer), **Follow-ups**. If it does not exist and you are running
under `full-send` or `full-stop`, create it from the thread first (their
step 1). Without either, the PR description and the thread are the contract.

## 1. The review engine

**`npertuset/*` repos:** the reviewer is the `@squirrel-agent` bot, driven
by the `squirrel-review-loop` skill. Call it with the mode and reviewer from
TODO.md (default: Agent reviews + local fixes, Debate). It skips its own
approval prompt when called from here. It posts the command, reads the
bot's findings, and hands them to you for triage. Each round you fix locally,
commit, push, and re-trigger. That skill never merges and neither does this
one.

**Anywhere else:** the repo's own review bots and CI. Use tstack's
`scripts/pr-wait` from this skill's directory as the watcher when
`watch_pull_request` is not available.

There is no CI on techchutes. Run every check its `CLAUDE.md` names
(`typecheck`, `build`, `check:css`, the docs generators when their folders
changed) before every push, and say in the PR when e2e could not run.

## 2. Waiting

Never write your own watcher, polling loop, or `sleep` loop. One watcher per
PR.

**In T3 Code:** handle the existing checks and comments first, then call
`watch_pull_request` and end your turn. T3 wakes you when a check fails,
required checks pass, someone comments or reviews, or the branch conflicts.

- Only the thread that owns the PR watches it. A delegated child (a council
  reviewer, any `delegate_task` child) never calls `watch_pull_request`.
- A wake is news, not a merge decision. Check the merge gate yourself.
- Unwatch when you hand off. When you stop (ready, blocked, or asking a
  question), call `unwatch_pull_request` first. A merge or close ends the
  watch on its own.
- "Stopped watching, could not read it" usually means GitHub's rate limit.
  `gh api rate_limit --jq .resources.graphql`; if `remaining` is near 0, wait
  for `reset` with one background command, then watch again.

The bot's review arrives as a PR comment, so the watch wakes you for it. The
`poll-review.sh` script in `squirrel-review-loop` is the fallback when no
watcher exists.

**Everywhere else:** `pr-wait <pr> [--repo owner/name] [--until ready|green|any-change]`
from this skill's `scripts/` folder, run through the Monitor tool
(`timeout_ms: 3600000`) so each line wakes you. Restart it after every push.

With either watcher: when an event needs no action, end your turn without a
message. Never post or say "still waiting".

## 3. Triage every finding against the contract

Only act on checks and comments newer than the latest push. Verify every
finding against the source before changing code. Then sort it:

| Finding | Do |
|---|---|
| Real bug in the intended case | Fix with the smallest change. Prefer deleting or narrowing code. Get proof before pushing. |
| Real bug outside the intended case, or in code this PR did not touch | Decline in writing, list under Follow-ups in TODO.md and the PR. |
| Contradicts a **Decision** in TODO.md | **Never apply it.** Reply with the decision and its date (`leaving-pr-comments` decline template), resolve the thread, tell the bot not to raise it again. If you think the decision was wrong, stop and ask the user with both sides in three lines each. |
| Widens the goal: new option, new guard, new abstraction, "while we're here" | Decline in writing. Follow-up. |
| Tests, compat, edge-case guards the intent does not need; small perf | Decline in writing. Follow-up. |
| Style that hides no bug | Ignore unless the repo's rules require it. |
| CI or check failure | Fix if the repo caused it; say so if infrastructure flaked and re-run. |

Reply with a written reason when dismissing anything, using
`leaving-pr-comments`. Resolve the comment after.

Keep the PR at the size the goal needs. Review loops grow a PR one
cheap-looking fix at a time. After each round run
`git diff --shortstat origin/<base>` and compare with the round before; if
the diff grew for reasons other than a real bug, cut first.

**The bot keeps repeating a declined point:** after the second time, stop
and ask the user (`AskUserQuestion`) with the point, your reason, and a
recommendation. Do not fix it to end the loop.

## 4. Base branch

Keep an eye on changes to the base branch. `pr-wait` reports when new base
commits touch this PR's files and when the PR becomes BEHIND or DIRTY.
`watch_pull_request` reports conflicts only, so check for BEHIND yourself
(`gh pr view --json mergeStateStatus`) before calling the PR ready. Rebase
with `git fetch && git rebase origin/<base>`, push with
`--force-with-lease`, run the checks again, re-request the review.

If an overlapping PR makes this one obsolete, stop, report it, and ask
before closing anything.

## 5. Rounds and the stopping rule

- Count each bot review as one round. Budget: 5 rounds, like
  `squirrel-review-loop`. Extend only for security, permissions, data loss
  or concurrency findings that are real and still open.
- Stop early when a round returns only nits.
- **Ready:** the latest review says good to merge **and** covers the current
  head, every check is green, mergeStateStatus is CLEAN, no human review
  requests changes. Right before declaring ready, `git fetch` and check the
  PR once more.
- **Needs the user:** a decision conflict, a repeated point, the budget
  reached, or a fix that needs a schema or design choice.
- **Blocked:** a check that fails for reasons outside the repo, a rejected
  push, the bot timing out twice.

## 6. Report

Start with the status heading from `~/.claude/CLAUDE.md` (✅ GOOD TO MERGE,
🔁 FIXES PUSHED, ⚠️ NEEDS YOUR DECISION, ⏳ WAITING FOR REVIEW, ❌ BLOCKED)
and the PR on the next line. Then: rounds, commits pushed per round, findings
fixed, findings declined with the one-line reason, follow-ups, and that
merging is manual unless `full-send` is running. On ready, hand back to the
caller (`full-send` merges; `full-stop` and a direct call stop here).
