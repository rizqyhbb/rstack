# rstack

Rizqy's fork of [t3dotgg/tstack](https://github.com/t3dotgg/tstack): the
autonomy skills, adapted for a Claude-only setup, T3 Code, and the Squirrel
and techchutes repos. Personal settings (merge rights, tracker, review bot,
worktrees, docs) live in `~/.claude/CLAUDE.md` under "Autonomy skills
(rstack)", so upstream changes can be merged without losing them.

## Skills

| Skill | Say | What it does |
|---|---|---|
| `full-send` | "full send" | Owns the thread to a merged PR: tracker, build, proof, docs, council, PR, review loop, change report, merge, wrap-up. |
| `full-stop` | "full stop" | Same, but stops with the PR ready for you to merge. Never merges. |
| `council` | "council" | Three fresh-context Claude reviewers (correctness, scope & decisions, proof & UX), looped until they agree. |
| `babysit-pr` | "babysit", "loop review" | Watches a PR through the review bot and checks; fixes real findings, never widens the PR or reverses a decision. |
| `file-pr` | "file a PR" | A PR that leads with the problem, with proof, decisions and the ClickUp link. |
| `change-report` | "make the report" | Local HTML before/after report with red marks. Never committed. |
| `wrap-up` | "wrap up", "clean this wt" | After the merge: worktree, containers, `.fullsend/`. Branch stays. |
| `takeover` | "take over" | Finishes someone else's (or an old thread's) PR, branch or thread, keeping their credit. |
| `modernize` | "modernize" | Rebases an old PR and decides MODERNIZE / REWORK / CLOSE. |
| `leaving-pr-comments` | (automatic) | Formats comments posted on your behalf; never `@agent`. |
| `squirrel-review-loop` | "loop review" | Drives `@squirrel-agent` on `npertuset/*` PRs. Never merges. |
| `new-feature` | `/new-feature` | Creates a Squirrel feature workspace (`wt new`). |
| `daily-squirrel-summary` | `/daily-squirrel-summary` | Daily activity and PR report from session transcripts. |

Dropped from upstream: `sol-loop` (needs GPT Sol; its budget and ledger
rules live in `council`).

## Install

```bash
git clone git@github.com:rizqyhbb/rstack.git ~/Documents/project/rstack
for s in ~/Documents/project/rstack/skills/*; do ln -s "$s" ~/.claude/skills/$(basename "$s"); done
```

## Updating from upstream

```bash
git fetch upstream && git merge upstream/main
```

## Requirements

- An authenticated GitHub CLI (`gh`).
- `python3` for `babysit-pr`'s `pr-wait` and `change-report`'s builder.
- T3 Code for `watch_pull_request`, the preview tools and `t3_thread_read`;
  everything falls back to native tools without it.

## License

[MIT](LICENSE), as upstream.
