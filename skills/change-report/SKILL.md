---
name: change-report
description: Build a local HTML before/after report of a branch's visible changes - screenshots from main and from the branch with red boxes on what moved, summary first. Use when the user says "make the report", "change report", "before/after", and as the last step before merge in full-send and full-stop.
---

# Change report

One HTML file the user looks at before saying "merge" and can forward to the
client. It is **local only**: `.fullsend/report/index.html` in the
worktree, excluded through `.git/info/exclude`, never committed, never
uploaded, deleted by `wrap-up`. It contains customer data from the test
database, so it does not go to an artifact service either.

## 1. What changed, as screens

From `git diff --stat origin/<base>` list every route, page, dialog, email
or CLI output a person can see that this branch changes. One entry per
screen and state (for example "PO page, Items tab, Received chip", "Create
outbound dialog, result"). Backend-only changes get one entry each with the
command and its output instead of a screenshot. Read `.fullsend/TODO.md` if
it exists; its Goal decides which screens matter most and go first.

## 2. Data

Use the test database, never staging or production. techchutes:
`E2E_TEST=1 npm run dev` on the test DB (`CLAUDE.md` → running locally).
Any step that seeds, resets or truncates that database runs under
`~/.claude/skills/full-send/scripts/with-testdb-lock <db-name> <command>`
(see full-send → Shared test database), because other threads use the same
database at the same time. Plain screenshots of existing data need no lock.
Squirrel: the shared dev database through `wt up`. Pick real records that
show the change (the same record for before and after). Note their ids in
the report.

## 3. After shots, then before shots

**After:** run the branch, open each screen, capture a full-page screenshot.
Both themes when the app has them (techchutes: light and dark). Use the
T3 Code preview tools (`preview_open`, `preview_resize`, `device_screenshot`)
or Playwright from the repo. Width 1440 unless the change is mobile. Save as
`.fullsend/report/shots/after-<n>-<theme>.png`.

**Before:** the same screens on the base branch with the same data.

- techchutes and other T3 worktrees: run the **main checkout** on another
  port (`PORT=3001 E2E_TEST=1 npm run dev` from `~/Documents/project/squirrel/techchutes`)
  against the same test DB. Never check out `main` inside the feature
  worktree. If the branch added a migration, the main checkout may not read
  the new column; say so and capture what it shows.
- Squirrel monorepo: ports are fixed by Auth0, so only one checkout runs.
  Capture the after shots, `wt down <branch>`, `wt up main <app>`, capture
  the before shots, then `wt up <branch> <app>` again. If another checkout
  holds a port (`wt up` exit 3), do not `--kill`; use the fallback.
- Fallback when a before shot is impossible: use a screenshot taken earlier
  in the thread of the same screen, and label it with its date. If none,
  write "no before capture" and describe the previous state in one line.

Save as `.fullsend/report/shots/before-<n>-<theme>.png`.

## 4. Red marks

Do not edit the PNGs. Each shot gets a list of boxes drawn over it by the
page: `x, y, w, h` in image pixels and a short label ("new column",
"badge moved under the numbers", "warning banner"). Find the coordinates by
comparing before and after; a `device_screenshot` of a bounded element or
Playwright's `boundingBox()` gives exact numbers. Mark what changed, not the
whole page. Three to five boxes per shot at most.

## 5. Build the page

Write `.fullsend/report/report.json`:

```json
{
  "title": "PO page: received, shipped, ship-to and tracking per item",
  "branch": "feat/po-items-dates", "pr": "https://github.com/npertuset/techchutes/pull/133",
  "date": "2026-11-12", "summary": ["one sentence per change, in order of importance"],
  "rules_bent": [{"rule": "…", "what_instead": "…", "how_you_see_it": "…"}],
  "screens": [
    {"name": "PO SWB-P02508, Items, All", "record": "po 62", "theme": "light",
     "before": "shots/before-1-light.png", "after": "shots/after-1-light.png",
     "boxes": [{"on": "after", "x": 880, "y": 420, "w": 420, "h": 36, "label": "new Shipped column"}],
     "note": "one line on what to look at"}
  ],
  "not_shown": ["backend-only changes, with the command and its output"]
}
```

Then run `python3 <this skill's dir>/scripts/build-report.py .fullsend/report`
(absolute path to the skill: `~/.claude/skills/change-report/scripts/build-report.py`).
It inlines the images as base64 and writes `index.html`: the summary first,
then a "where it bends the normal flow" table when `rules_bent` is not empty,
then each screen as before | after with the boxes drawn, then the
not-shown list. One self-contained file.

## 6. Exclude and open

```bash
grep -qx '.fullsend/' .git/info/exclude || echo '.fullsend/' >> .git/info/exclude
git status --short   # .fullsend must not appear
```

Open it for the user in the thread (T3 Code: `html_preview` then
`html_render` of the file, or `preview_open` on a `file://` URL) and give the
absolute path. In the final message, list each screen in one line. Do not
describe the screenshots in prose; the page does that.
