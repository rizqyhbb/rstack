---
name: file-pr
description: File a concise pull request that leads with the problem. Use when the user asks to file, open, or create a PR, and from full-send, full-stop and takeover.
---

# File PR

Before filing, check whether a PR for this branch already exists
(`gh pr view --json number,url,state`). If it does, update it instead of
opening a second one. Review the diff locally against the base branch
(usually `origin/main`) to make sure its contents match the goal, and that
nothing in `git status` is a stray file (`.env`, generated env files,
`.fullsend/`, screenshots).

## The repo's own rules come first

Read the repo's `CLAUDE.md` section on pull requests and follow it: which
checks to run before filing, how the changelog entry is written, whether the
PR number has to go into the changelog after creation (techchutes), the
assignee, how files are staged (name them, never `git add -A`). Rebase on the
latest base branch first (`git fetch && git rebase origin/<base>`), and report
any conflict you had to resolve.

If the repo's rules say to ask the user something with `AskUserQuestion`
(for example which reviewers to request) and you are running under
`full-send`, `full-stop` or `takeover`, do not ask. Use what
`.fullsend/TODO.md` records, otherwise the default in that repo's rules, and
list the choice in your report. Reviewer requests default to none.

## Title

PR titles usually become commit messages, so follow the repository's title
conventions. Look at recently merged PRs and Git history for examples. Prefer
a concise, human-readable title that explains why the change matters.
Describe what a person sees, not what the code is called.

BAD

> ❌ perf(server): negotiate permessage-deflate on the websocket

GOOD

> ✅ perf(server): cut websocket frame size by 70%+ with gzipping

In techchutes the title is the same sentence as the changelog entry.

## Description

Open with a simple explanation of the problem based on the user's original
prompt, then briefly explain the solution. Do not lead with an implementation
inventory. Then, in this order, only the parts that apply:

1. **Problem** in the user's words, one or two sentences.
2. **What changed**, as a person sees it. Screens and behaviour first, file
   names last if at all.
3. **Proved by**: one line per kind of proof (reproduced and fixed, checks
   run, app run and looked at, e2e). Say what could not be run and why.
4. **Decisions** made in the thread that a reviewer might otherwise question,
   with their dates, copied from `.fullsend/TODO.md`. This is what stops the
   review bot from reopening them.
5. **Follow-ups**: things seen and deliberately left out.
6. **ClickUp**: the task link, when there is one.
7. Attribution: `Created with <model> in <harness>.` using the model name the
   harness reports (never guess), plus any attribution line the harness asks
   for.

BAD

> ❌ Removed implicit workspace carry-over from every "new thread" entry point (cmd+n / cmd+shift+o, sidebar v1/v2 buttons, command palette). New threads inherit only the project from context; branch, worktree, and env mode always come from the configured defaults. Deleted buildContextualThreadOptions, startNewThreadInProjectFromContext, and the v1 sidebar's seed-context machinery.

GOOD

> ✅ My "new worktree" default was ignored when starting new threads on existing worktrees. Super unintuitive. Now your preferences always apply.

Before submission, check the title, description, quotes, and attachments for
secrets and private details: connection strings, customer names and emails
from test data, internal URLs.

## Filing

Open a real PR rather than a draft so review bots run:

```bash
gh pr create --assignee "$(gh api user --jq .login)" --base <base> --title "..." --body-file <file>
```

If `gh pr create` fails because the GraphQL rate limit is used up, open it
through REST with
`gh api repos/<owner>/<repo>/pulls -f title=... -f head=... -f base=... -F body=@<file>`.

If the user also asked to babysit it, or you are inside `full-send` or
`full-stop`, continue with the `babysit-pr` skill.

Do not post a follow-up PR comment unless it serves the user's request. When
a comment is needed, use the `leaving-pr-comments` skill.
