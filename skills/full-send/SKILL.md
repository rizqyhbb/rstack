---
name: full-send
description: Trigger this if the user says 'full send'. Own the thread end to end - tracker, build, proof, docs, council, PR, review loop, change report, merge, wrap-up - without asking unless only the user can decide.
---

# Full Send

If the user triggered this, it's because they are not watching this thread,
and they want you to complete the work end-to-end autonomously. Your updates
and your final message go unread until long after you stop. You own the work
from its current state to a merged PR, a change report, and a clean machine.

If the user did not explicitly say "full send" (or a clear equivalent such
as "babysit it, merge it, I'm leaving"), do not assume full autonomy. If
they did, everything below applies.

Settings this skill reads: the **Autonomy skills (rstack)** section of
`~/.claude/CLAUDE.md` (merge rights, tracker, reports, review bot,
worktrees, docker, docs, decisions) and the repo's own `CLAUDE.md`. The
repo's rules on *how* to do things (checks, changelog, staging files) always
apply. Only their *ask first* steps are replaced by this request.

The user grants you permission to:

- Merge the PR once the merge gate passes, in any repo under `~/Documents`.
- Force-push the PR's own branch with `--force-with-lease` after a rebase.
- Use the test methods that Proof needs without asking first: running the
  app or a dev server, browser automation, screenshots, the preview tools,
  simulators. Rules that name the correct command, fixture or database still
  apply (techchutes: the test DB, never `DATABASE_URL`; Squirrel: `wt up`,
  never `npm run dev` or `docker compose up` by hand).
- Remove the feature's worktree and its containers after the merge.

It does not grant: production or staging data changes, deleting data,
migrations on a shared database without telling the user, closing PRs,
force-pushing any other branch, touching the main checkout, or bypassing a
harness approval prompt.

## Where you are

Run `pwd && git branch --show-current; git worktree list` first.

- **Feature worktree** (Squirrel `wt/<feature>/squirrel-api`, a T3
  worktree, any non-main checkout): proceed.
- **Main checkout** of a repo, or the default branch: do not work here.
  Squirrel: `wt new <branch>` and tell the user to open the workspace (their
  rule). Other repos: create a branch and a worktree, then continue there.
  Never commit feature work on `main`.

## Steps

1. **Tracker.** Create `.fullsend/TODO.md` (add `.fullsend/` to
   `.git/info/exclude`). Sections: **Goal** (one sentence, in the user's
   words), **Out of scope**, **Decisions** (every choice already made in the
   thread, with today's date and the reason, plus the ones you make from
   here), **Review** (mode and reviewer for the bot, default Agent reviews +
   local fixes, Debate), **Steps** (this list as checkboxes), **Follow-ups**.
   If the thread was compacted, rebuild Decisions from the summary and the
   diff. Keep it current; it is read by every reviewer and every loop round.
2. **Finish the change** with the smallest change that works. Fix the case
   that happened, not every case that could. Ideas found on the way go under
   Follow-ups, never into the diff. Small, focused commits with the repo's
   staging rules (name files, never `git add -A`).
3. **Prove it.** See "Proof".
4. **Docs.** Update what the repo's `CLAUDE.md` names: `DESIGN.md`,
   `docs/*`, generated guides and their `--check`, `CHANGELOG.md` with the
   repo's format (techchutes: the entry needs the PR number, so it is
   committed right after step 6). Done before review, not after.
5. **Council** (`council` skill). Fix real findings, decline the rest in the
   ledger. Decisions stay.
6. **File the PR** (`file-pr` skill). Rebase on the latest base branch
   first. The description carries the problem, the proof line, the
   Decisions, the ClickUp link when known, and the council table.
7. **Babysit** (`babysit-pr` skill): the bot loop, checks, rebases. Proof
   for each fix before it is pushed. Wait with `watch_pull_request`, never a
   sleep loop. If you end the turn while something is pending, nobody will
   prompt you again, so stay with the watcher.
8. **Change report** (`change-report` skill). Before/after with red marks,
   local only, opened in the thread.
9. **Merge gate, then merge.** See below.
10. **Wrap up** (`wrap-up` skill): worktree, containers, `.fullsend/`.
    Branch stays.
11. **Report** in the final message: the PR link, the merge commit, the
    proof, every decision made for the user, follow-ups, what was cleaned
    up, and the report path (it was deleted with the worktree unless the
    user asked to keep it; say which).

Stay active from step 1 to step 11. If you stop before the merge, call
`unwatch_pull_request` first.

## Proof

Proof is evidence you observed yourself in this session: command output, a
reproduction, a screenshot. Use the most direct proof the change allows:

- Reproduce the original failure, apply the fix, then watch the same
  reproduction pass.
- Run the checks the repo's CI runs, or, where there is no CI (techchutes),
  every check its `CLAUDE.md` lists.
- Add one focused test that fails without the fix, when the behaviour has
  none and the repo has a test setup.
- For UI and runtime behaviour, run the app and look at the change. Green
  mocked tests do not prove the user experience works. The screenshots feed
  the change report.

When you cannot find a way to prove a change, you do not have full
confidence. Ask the user.

### Shared test database

Several threads usually run at once on the same repo, and they all point at
the same test database (techchutes: `TEST_DATABASE_URL`, whose e2e suite
truncates every table). Two runs at once corrupt each other and look like
regressions. So every command that writes to a shared test database (e2e,
an import with `--reset`, a seed, a screenshot run that seeds) goes through
the lock script in this skill's folder:

```bash
~/.claude/skills/full-send/scripts/with-testdb-lock techchutes-test npm run test:e2e -- tests/e2e/foo.spec.ts
~/.claude/skills/full-send/scripts/with-testdb-lock techchutes-test npx tsx scripts/with-test-env.ts npm run -s import:workbook -- ~/Downloads/workbook-tc --reset --apply
```

The lock name is the database's name (one per database, shared by every
thread). It waits for the holder, prints who holds it, clears a lock whose
process is gone, and releases on exit. Never wait on another thread's
Playwright process by `ps` instead; that misses CLI imports and seeds. If
the wait exceeds 40 minutes the script gives up and says who holds it: run
the proof later, do not kill the holder. Reads and the dev server need no
lock. `change-report` and `babysit-pr` use the same script.

## Merge gate

Full confidence means all of these are true on the latest commit:

- Your proof covers every change in the diff.
- Required checks are green (or, with no CI, every local check passed on the
  final head and the PR says so).
- The review bot's latest verdict is good to merge **and** covers the current
  head. Every finding is fixed or declined with a written reason. A verdict
  whose only remaining disagreements are recorded Decisions you declined in
  writing counts as good to merge for those items.
- No human review still requests changes.
- The branch is up to date with the base and GitHub reports it mergeable
  (`mergeStateStatus` CLEAN, not BEHIND or DIRTY).
- The change report exists and was opened in the thread.

Right before merging, `git fetch` and check the PR again. Merge with the
method the repo uses (recent merged PRs show it; both Squirrel repos squash).
If the repo uses auto-merge or a queue, stay until GitHub reports the PR as
merged. Never `--admin` or any bypass. Never merge a different PR.

## Asking the user

A question in a normal message goes unseen, and the thread looks done. Use
`AskUserQuestion` so the thread shows that it is waiting. Put all the context
in the question: the PR link, what blocks you, the options with your
recommendation first.

Ask only when you cannot continue alone:

- You cannot prove the change.
- The merge gate cannot pass, and you cannot fix that yourself.
- A review finding contradicts a Decision and you think the decision was
  wrong (both sides, three lines each). If you think the decision stands,
  decline the finding and do not ask.
- The next step is outside the grant above: deleting data, production or
  staging data, a migration on a shared database, closing a PR,
  force-pushing another branch.
- The goal is ambiguous in a way that changes the result.
- Another PR makes this one obsolete.
- The review bot repeats, twice, a point that no Decision covers, or the
  round budget ends with such a point still open. A point a Decision
  covers is never a reason to ask: decline it again and move on.

Decide everything else yourself with sensible defaults, record each decision
in `.fullsend/TODO.md` with the reason, and list them in the report.

If no question tool is available, or it returns no answer, take the safe
path: leave the PR open and unmerged, keep the worktree, and start your
final message with the question under the `⚠️ NEEDS YOUR DECISION` heading.
