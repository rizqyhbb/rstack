---
name: squirrel-review-loop
description: Run the @squirrel-agent PR review loop on a squirrel repo PR (npertuset/* only) — trigger the review agent, poll for its feedback, then either fix it locally (commit + push) and re-trigger until the PR is clean, or start the agent's own `review loop` (it reviews and fixes up to 10 rounds) and monitor it. Never merges. Use when the user says "loop review", "review loop", "squirrel review", "run squirrel-agent review", "babysit this PR", or asks to get a squirrel PR reviewed by the review agent.
argument-hint: "[pr-number]"
---

# Squirrel review loop

Drives the `@squirrel-agent review` bot on a GitHub PR: **review → feedback → commit → push → re-review**, repeated until the PR is clean. This skill **never merges** — merging is always done manually by a human.

## 0. Guard — squirrel repos only

Run first and stop if it fails:

```bash
git remote get-url origin
```

The remote must be `github.com:npertuset/<repo>` or `github.com/npertuset/<repo>`. Squirrel PRs are almost always in `npertuset/squirrel-api`, the monorepo that holds every app (`api/`, `admin/`, `web/`, `web-next/`, `cms/`, `brain/`); other `npertuset/*` repos such as techchutes work too. squirrel-admin, squirrel-cms and squirrel-gatsby-sanity are archived (read-only): if the PR is there, tell the user and stop. If the remote isn't `npertuset/*`, tell the user this skill only works in the squirrel repos and stop. Don't post anything.

## 1. Resolve the PR

- If `$ARGUMENTS` has a PR number, use it. Otherwise use the PR for the current branch: `gh pr view --json number,url,headRefName,baseRefName,state`.
- `REPO` = `npertuset/<repo>` from the remote. `PR` = the number.
- The PR must be `OPEN`. The local branch must equal `headRefName` (check out the PR branch with `gh pr checkout <PR>` if it doesn't) and be up to date with its remote (`git pull --ff-only`).
- `git status` must be clean. If there are uncommitted changes, stop and ask the user. Never stash or discard them yourself.

## 2. Approval gate (once per skill invocation)

**Skip this gate when a caller already holds the answers.** If this skill was invoked by `full-send`, `full-stop` or `babysit-pr`, the "full send" / "full stop" request is the approval: use the loop mode and reviewer they pass (default: **Agent reviews, local fixes** with **Debate**, or whatever `.fullsend/TODO.md` records under Review), build `CMD_REVIEW` from that, and do not ask. Everything else in this skill still applies, including never merging.

Before posting anything, use **one** `AskUserQuestion` call with **two questions** (when there are several PRs, ask once for all of them):

**Question 1, "Loop mode":** "Run the @squirrel-agent review loop on `<REPO>#<PR>` (`<headRefName>`)? It posts PR comments and never merges. Who fixes the findings?"

1. **Agent reviews, local fixes** — the bot reviews, and you triage and fix locally, then commit + push each round without asking again (steps 5–7).
2. **Agent review loop** — the bot runs its own review → fix loop (up to 10 rounds) from one `review loop` comment. You check the PR context, trigger it once, and monitor each round. You never commit or push code (step 6b).
3. **Review only** — trigger one review, triage it, and show the proposed fixes locally. Stop before committing.
4. **Cancel** — post nothing.

**Question 2, "Reviewer":**

1. **Debate (default)** — Claude reviews, Codex challenges. Nothing is added to the command.
2. **Codex only** — add ` codex only` to every command.
3. **Claude only** — add ` claude only` to every command.

If the user adds a focus note (via "Other" or the option notes), it goes after the command, separated by ` — `.

Build the command once and reuse it every round: `CMD_REVIEW` = `@squirrel-agent review[ codex only|claude only][ — <focus>]`, and `CMD_LOOP` is the same with `review loop` (Agent review loop mode only).

This approval covers **only this invocation** of the skill. The next time the skill is called, ask again. Approval never extends to merging, force-pushing, rebasing, or touching any branch other than the PR head.

### Bot command rules

- Always use the `@squirrel-agent` form. **Never `@agent`**, because it notifies the owner of the bot's GitHub account. The bare `review` / `fix` / `review loop` comments also work, but they can't carry a reviewer choice or a focus note.
- The command must be a comment of its own. A command inside a quote or a code block is ignored, so never quote one in an update comment if you want it to run.

## 3. Trigger a review

**Agent review loop mode only:** post `CMD_LOOP` instead of `CMD_REVIEW` (same command, same id/timestamp capture), and only once per invocation. Before that, read the PR description (and the linked ClickUp task, if there is one). The bot only knows what's written there. If the goal, scope, constraints or out-of-scope items are missing, draft an improved description, show it to the user, and only update it (`gh pr edit --body-file`) once they OK it.

Post a comment that is exactly `CMD_REVIEW` (nothing else in it) and record its id and timestamp:

```bash
gh api repos/$REPO/issues/$PR/comments -f body="$CMD_REVIEW" \
  --jq '{id: .id, created_at: .created_at}'
```

The bot reacts to that comment with 👀 when it picks it up, then posts a comment containing the hidden marker `<!-- squirrel-agent:review -->`. **The bot posts from the `npertuset` account (same as the repo owner), so detect reviews by the marker, never by the author.** A review takes 20–60 min.

## 4. Poll for the review

Start the poller with the Bash tool and **`run_in_background: true`** (you get re-invoked when it exits, so don't also poll by hand):

```bash
bash ~/.claude/skills/squirrel-review-loop/poll-review.sh "$REPO" "$PR" "$TRIGGER_ID" "$TRIGGER_CREATED_AT"
```

(Always use this absolute path; the skill lives in `~/.claude/skills`, so it is available from every checkout and worktree.)

It checks every 7 min (within the requested 5–10 min window) and warns if there's no 👀 after the first check. It exits with:
- `REVIEW_POSTED comment_id=<id>` → continue to step 5.
- `TIMEOUT` (90 min by default) → tell the user the review agent didn't respond, and ask whether to keep waiting, re-trigger, or stop.

While it runs, tell the user it's waiting, then stop and wait for the notification.

## 5. Read and triage the feedback

Fetch the full review: `gh api repos/$REPO/issues/comments/<id> --jq .body`. Also re-read any **human** comments posted since the last round (scope clarifications from maintainers override the bot).

Sort every finding into exactly one bucket. Verify each one against the actual code first; the bot is sometimes wrong.

| Bucket | Criteria | Action |
| --- | --- | --- |
| **Fix** | Real and inside this PR's scope | Fix it |
| **Disagree** | Wrong on the facts, or the current code is intentional | Don't change the code; write down why, with file:line evidence |
| **Out of scope** | Pre-existing, unrelated to this PR's diff, covered by another task/PR, or would expand the PR | Don't fix; note it (and link the other PR/task if there is one) |

Don't let the bot expand the PR. When in doubt, choose **Out of scope** and flag it for the user rather than growing the diff.

## 6. Fix, verify, commit, push

- Make only the **Fix** changes.
- Run the checks of every app the PR touches before committing. In the monorepo, list them with `git diff --name-only origin/main...HEAD | cut -d/ -f1 | sort -u`, then run each app's lint, typecheck and relevant tests from its own folder (`cd admin && npm run lint`), as its `CLAUDE.md` / `package.json` describe. The root has no `package.json`. If they fail, fix them or report it. Never push red.
- Commit using the repo's commit conventions (check `git log --oneline -10`), one commit per round, e.g. `fix: address squirrel-agent review round N`. Stage the specific files you changed; never `git add -A`.
- `git push` to the PR head branch. **No force-push, no rebase, no amend.**
- In **Review only** mode: stop here, show the diff and the triage table, and end the loop.
- If a round has **no Fix items**, skip committing; go straight to step 7 or 8.

## 6b. Agent review loop mode (instead of steps 6–7)

The single `CMD_LOOP` comment from step 3 makes the bot review, fix, push and re-review by itself, **up to 10 rounds**. You don't edit, commit or push code, and you don't post `review` / `fix` commands while its loop runs. Each time the poller reports `REVIEW_POSTED`:

1. Fetch the review and triage it as in step 5 (only to report it; the bot decides what to fix). Count the marker reviews posted since the `CMD_LOOP` comment; that count is the bot's round number.
2. Decide whether the bot's loop has ended. It has ended when any of these holds:
   - the review says `AGREE: GOOD TO MERGE`, or has no Fix items left;
   - it is the 10th review since `CMD_LOOP`;
   - the bot posted a comment saying the loop finished or stopped (if you see one, note its wording/marker for the user so the skill can detect it directly).
3. **Not ended:** report the round with `# ⏳ WAITING FOR REVIEW` (bot round N/10, its commits, the new findings, anything you'd triage as Disagree / Out of scope). Restart the step 4 poller with the `CMD_LOOP` comment's id and **this review's `created_at`** as the timestamp, and wait.
4. **Ended:** `git pull --ff-only` and run the checks of every app the PR touches (as in step 6). If they're red, report `# ❌ BLOCKED`, and don't fix it yourself unless the user says so. Then go to step 8.

To steer the bot mid-loop (it keeps fixing something you'd triage as Disagree / Out of scope, or it's expanding the PR), stop and tell the user (`# ⚠️ NEEDS YOUR DECISION`). Don't post comments to it on your own. If the loop ends with Fix items left, offer another `CMD_LOOP` (with a focus note listing what to skip) or switching to **Agent reviews, local fixes**, and let the user pick.

Skip the step 7 update comment in this mode. The bot's own comments are the record.

## 7. Post the update, then re-trigger

Post **two separate comments**, in this order:

1. **Update comment** (the round summary):

   ```md
   ### Round N — addressed squirrel-agent review

   **Fixed** (<short-sha>)
   - `path:line` — what changed

   **Disagree**
   - `path:line` — why (evidence)

   **Out of scope** (not fixed in this PR)
   - `path:line` — why / tracked in <link>
   ```

   Leave out empty sections.

2. **Trigger comment** — exactly `CMD_REVIEW` (must be its own comment), and record the new id/timestamp.

Go back to step 4.

## 8. When to stop

Stop the loop and report to the user when any of these holds:
- The latest review has **no Fix items** left (clean, or only Disagree / Out-of-scope items you've already explained). Post a final update comment and **don't** re-trigger.
- The bot keeps repeating findings you've already disagreed with (2 rounds in a row) → stop and let the user decide.
- **5 rounds** have completed (local-fix mode) → stop and ask whether to continue. In Agent review loop mode the bot caps itself at 10 rounds; stop when its loop ends (step 6b).
- A fix would need a design decision, a new dependency, a schema/migration change, or touching code outside the PR's scope → stop and ask.

Final report to the user: the rounds run, the commits pushed (SHAs), the remaining Disagree / Out-of-scope items, and the PR URL, with a reminder that **merging is manual**.

**Every message to the user about this loop starts with a status heading** (defined in the user's global `~/.claude/CLAUDE.md`, "Start PR review reports with a status heading"), then `<repo>#<PR> — <PR URL>`, then the details:

- `# ✅ GOOD TO MERGE` — the latest review is `AGREE: GOOD TO MERGE` **on the current head commit** (if you pushed after it, re-trigger and use 🔁)
- `# 🔁 FIXES PUSHED — RE-REVIEW REQUESTED` — this round's fixes are pushed and a new review is requested (say the round)
- `# ⚠️ NEEDS YOUR DECISION` — any step 8 stop that needs the user: repeated disagreement, design/schema decision, round limit
- `# ⏳ WAITING FOR REVIEW` — a review is requested and pending (also when resuming after a session restart)
- `# ❌ BLOCKED` — `TIMEOUT`, red checks, or a rejected push

One heading section per PR when a message covers several PRs.

## Hard rules

- **Never merge.** Never run `gh pr merge`, enable auto-merge, approve the PR (`gh pr review --approve`), or close it.
- Never force-push, rebase, amend pushed commits, or push to any branch other than the PR head.
- Only commit and push after the step 2 approval of the current invocation, and never in **Agent review loop** mode.
- Never trigger with `@agent`; always use `@squirrel-agent`.
- Never edit or delete other people's comments (or the bot's).
- Only work in `npertuset/*` repos that aren't archived (step 0).
