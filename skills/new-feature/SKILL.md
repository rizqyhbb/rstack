---
name: new-feature
description: Create a Squirrel feature workspace for a new or existing branch (a git worktree of the monorepo)
argument-hint: [short description of the feature]
---

Set up a new feature workspace. Feature description (may be empty): $ARGUMENTS

Do NOT write any feature code in this session. This session only creates the
workspace.

All Squirrel apps live in one monorepo, `npertuset/squirrel-api`
(main checkout `~/Documents/project/squirrel/squirrel-api`, apps in `api/`,
`admin/`, `web/`, `web-next/`, `cms/`, `brain/`). A workspace is one worktree
of it holding every app, so there are no repos to choose.

1. If the description is empty, ask me in one short question what the feature
   or fix is.
2. If the argument is (or names) an existing branch, or I say I want to
   continue existing work, use that branch: find it with
   `git -C ~/Documents/project/squirrel/squirrel-api fetch -q origin` and
   `git -C ~/Documents/project/squirrel/squirrel-api branch -a --list '*<name>*'`.
   If it is checked out in the main checkout, tell me and ask before switching
   that checkout to `main` (it must be clean first). If the branch predates
   the monorepo move (no `api/` folder on it:
   `git -C … ls-tree --name-only <ref> api`), tell me: it needs a rebase
   across the move (`docs/monorepo.md`) before it's usable.
   If it is NOT in the monorepo, also look in the old pre-monorepo checkouts
   that still exist (`~/Documents/project/squirrel/squirrel-admin`,
   `squirrel-cms`, `squirrel-gatsby-sanity`: same `branch -a --list`, no
   fetch, their GitHub repos are archived). Open PR branches were already
   moved into the monorepo, so a hit there is local-only work. Stop and tell
   me which repo has it and its last commit (`git log -1 --format='%h %cs %s'`),
   and that it must be imported into the monorepo first
   (`git -C <old repo> format-patch origin/main..<branch> --stdout` piped into
   `git am -3 --directory=<app>` inside a new monorepo workspace; `<app>` is
   `admin`, `cms`, or `web`/`web-next` for squirrel-gatsby-sanity, whose
   paths already start with them, so no `--directory` there; see
   `docs/monorepo.md`). Ask before doing the import. Never run `wt new` with that name before it's
   imported: it would silently create a new, empty branch.
   Otherwise propose a new branch name (`feat/…`, `fix/…` or `chore/…`,
   short kebab-case) and confirm it with me in one short question (use the
   AskUserQuestion tool if available), mentioning which apps you expect it to
   touch.
3. Check for clashes: run `wt ls` and
   `git -C ~/Documents/project/squirrel/squirrel-api branch --list '<branch>'`.
   If the branch already exists, say so and confirm I want to continue that
   existing work. If `wt ls` already shows 3 or more workspaces, mention it
   (disk is limited) and suggest removing stale ones.
4. Run `wt new <branch>`.
5. Reply with only:
   - the workspace folder `~/Documents/project/squirrel/wt/<feature>/`
   - how to run it: `wt up <branch> [api] [admin] [web|web-next] [cms]`
     (normal ports 7557 / 3000 / 8000 / 3333; it asks before stopping
     whatever holds them; `wt install <branch> <app>` first for any app
     without `node_modules`)
   - "Open a new T3 Code chat in this folder and describe the feature there."
