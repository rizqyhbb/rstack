---
name: wrap-up
description: Clean up after a merged PR - remove the feature worktree, stop and remove the containers only it used, delete the local .fullsend/ folder. Use when the user says "wrap up", "clean this wt", "clean up the worktree", or after a full-send merge.
---

# Wrap up

Leave the machine as if the feature never had a worktree: no checkout, no
containers, no dev server, no local tracker or report. Keep the branch and
the shared database. Never touch anything another checkout uses.

## 0. Where am I

```bash
pwd; git rev-parse --show-toplevel; git branch --show-current; git worktree list
```

Work out which repo and which checkout this is:

- **Squirrel monorepo workspace** (`~/Documents/project/squirrel/wt/<feature>/squirrel-api`).
- **T3 worktree** (`~/.t3/worktrees/<repo>/<branch>`).
- **Main checkout** of any repo: nothing to remove. If the user names a
  branch, find its worktree in `git worktree list` and continue with that.

Never wrap up a main checkout.

## 1. Confirm the work is finished

```bash
gh pr list --head <branch> --state all --json number,state,mergedAt,url
git status --short
```

- The PR must be **merged**. Closed without merge: ask (`AskUserQuestion`)
  whether to clean up anyway. No PR: ask.
- Uncommitted or untracked changes other than `.fullsend/` and the repo's
  generated env files: stop and list them. Never stash, discard or `--force`.
- Unpushed commits: stop and say so.

## 2. Dev servers and containers that belong to this checkout only

**Squirrel monorepo:** `wt status` shows who holds 7557 / 3000 / 8000 /
3333 and which containers run. `wt rm <branch>` (step 3) stops this
workspace's dev servers and its api + worker containers itself. Do not run
`docker compose down` by hand, and never stop the main stack (`squirrel_db`,
redis, mailhog) or another workspace's containers. If a port is held by a
different checkout, leave it alone.

**T3 worktree (techchutes, basebook-next):** these repos run no containers.
Find dev servers started from this worktree and stop only those:

```bash
lsof -nP -iTCP -sTCP:LISTEN | grep -E 'node|next' ; for p in <pids>; do lsof -p $p -Fn | grep -m1 '^n/' ; done
```

Kill a process only when its working directory is inside this worktree.
Also stop any Playwright or preview browser started from it.

**Any other repo:** look for a compose file in the checkout. If it has one,
`docker compose ps` from there and `docker compose down` (no `-v` unless the
volumes carry the worktree's name and nothing else uses them). Show what
will be removed before removing it.

## 3. Remove the worktree

**Squirrel monorepo:** `wt rm <branch>` from anywhere. It refuses on
uncommitted changes: report them, never `--force`. Then `wt ls`; if three or
more workspaces remain, say which look merged (`git branch --merged origin/main`).

**T3 worktree:** from the main checkout, so the command does not run inside
the folder it deletes:

```bash
git -C <main checkout> worktree remove ~/.t3/worktrees/<repo>/<branch>
git -C <main checkout> worktree prune
```

If this session's own working directory is that worktree, the removal still
works, but the shell is then in a deleted folder. Do it as the last command
of the turn and tell the user the thread can be closed.

Never `rm -rf` a worktree folder.

## 4. Local files

`.fullsend/` goes with the worktree. If the tracker or report lives
elsewhere (the user named a folder), delete only what this feature created
and say what you deleted. Report files the user asked to keep stay.

## 5. The branch

Keep it. Deleting the local or remote branch needs the user's OK
(`AskUserQuestion`), except when the repo auto-deletes merged branches on
GitHub, which you only report.

## 6. Report

Three lines: what was removed (worktree path, containers, servers, files),
what was kept (branch, database), and anything you did not do and why.
