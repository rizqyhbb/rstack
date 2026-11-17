---
name: daily-squirrel-summary
description: Summarize Claude Code activity across the squirrel monorepo (and the old pre-monorepo repos) over a date range, grouped by date then app, plus the PRs opened/merged/closed
argument-hint: "[start date] [to end date]"
---

# Squirrel Daily Summary

Your job is to produce a report with two sections:

1. **Activity** — read Claude Code session transcripts and write a plain-English summary: features, bug fixes, merges, releases, and brainstorming/design discussions only. **No code, no file paths, no implementation detail.**
2. **Pull requests** — PRs opened, merged, or closed in the range **that the user's Claude sessions worked on**, from GitHub: the apps it touches, title, head branch, the base branch it targets/merged into, and status.

Since 2026-10-07 all Squirrel apps live in one monorepo, `npertuset/squirrel-api` (`api/`, `admin/`, `web/`, `web-next/`, `cms/`, `brain/`). squirrel-admin, squirrel-cms and squirrel-gatsby-sanity were separate repos before that and are now archived; they still matter for date ranges before the move.

## Step 1 — Get the date range

If the user already supplied a start and/or end date in their invocation (e.g. `/daily-squirrel-summary 2026-08-17 to 2026-08-19`), use those. Otherwise ask with `AskUserQuestion` (or plain text if that tool isn't available) for:
- Start date
- End date (default: today, if the user only gives one date treat it as a single-day report)

Resolve relative dates ("yesterday", "this week") against today's actual date before proceeding.

### All dates are LOCAL time — never UTC

The user thinks in their machine's local timezone. Transcript timestamps are stored in **UTC**. Filtering or bucketing on the raw UTC string is wrong and will silently attribute early-morning and late-night work to the wrong day.

Before doing anything else, get the offset and compute the UTC window that corresponds to the requested local days:

```bash
date +"%Z %z"     # e.g. "WIB +0700"
# Local [start 00:00, end+1day 00:00) → UTC window, e.g. for +0700 and a single local day 2026-09-15:
#   2026-09-14T17:00:00Z  ..  2026-09-15T17:00:00Z
```

Do the conversion explicitly rather than by eye:

```bash
# macOS `date`: parse the local wall-clock to epoch first, then render the epoch as UTC.
# (Do NOT use `-u` on the parsing call — it makes the INPUT be read as UTC too.)
S=$(date -j -f "%Y-%m-%d %H:%M:%S" "<start> 00:00:00" +%s)
E=$(date -j -v+1d -f "%Y-%m-%d %H:%M:%S" "<end> 00:00:00" +%s)
START_UTC=$(date -u -r $S +"%Y-%m-%dT%H:%M:%SZ")   # e.g. 2026-09-14T17:00:00Z
END_UTC=$(date -u -r $E +"%Y-%m-%dT%H:%M:%SZ")     # e.g. 2026-09-15T17:00:00Z

# Offset in seconds, for converting timestamps back to local in jq:
OFFSET=$(( $(date +%z | cut -c1-3) * 3600 + $(date +%z | cut -c4-5) * 60 ))   # +0700 -> 25200
```

Sanity check before writing the report: for a positive offset like +0700, a local day **starts the previous afternoon in UTC**. If your candidate file list looks identical to a naive UTC-day filter, you probably didn't apply the offset.

## Step 2 — Scope to squirrel projects only

Squirrel Claude project directories live under `~/.claude/projects/` and are named with the prefix `-Users-rizqyhbb-Documents-project-squirrel`. This includes the squirrel folder itself (`-Users-rizqyhbb-Documents-project-squirrel`), the monorepo's main checkout (`…-squirrel-squirrel-api`, also a subfolder like `…-squirrel-squirrel-api-admin`), feature workspaces (`…-squirrel-wt-<feature>`, possibly with a `-squirrel-api…` suffix), the old pre-monorepo repos (`…-squirrel-squirrel-admin`, `…-squirrel-squirrel-cms`, `…-squirrel-squirrel-gatsby-sanity`, `…-squirrel-gatsby-sanity-web`), and side projects like `basebook-next` and `techchutes`. Do NOT include any other project directory (personal projects, kulina, mimo, or the bare `-Users-rizqyhbb` catch-all sessions).

Find session files (`*.jsonl`, including `subagents/*.jsonl`) under those directories. Treat mtime only as a **coarse pre-filter** — widen it by a day on each side, because a session can be written to long after the work happened, and a file whose mtime sits outside the range can still contain lines inside it. The authoritative filter is the per-line timestamp (Step 3).

```bash
find ~/.claude/projects -maxdepth 1 -type d -name '-Users-rizqyhbb-Documents-project-squirrel*'

# `find -newermt` interprets its argument in LOCAL time, so pass local dates here — but widen the window.
find <each matching dir> -name "*.jsonl" -newermt "<start-1day> 00:00:00"
```

Then keep only the files that actually contain lines in the UTC window, e.g. for local 2026-09-15 at +0700:

```bash
grep -cE '"timestamp":"2026-09-14T(1[7-9]|2[0-3])|"timestamp":"2026-09-15T(0[0-9]|1[0-6])' "$f"
```

Group activity by **app**, not by project directory: one directory (the main checkout or a workspace) now covers every app.

- Monorepo directories (main checkout, `wt-<feature>` workspaces): take the app from the paths the session worked in (`…/squirrel-api/api/…` → **API**, `/admin/` → **Admin**, `/web/` → **Web**, `/web-next/` → **Web-next**, `/cms/` → **CMS**, `/brain/` → **Brain**; root files only, e.g. workflows or `CHANGELOG.md` → **Repo**). A session that touched several apps contributes to each; describe a cross-app feature once, under the first app, and name the others ("API + Admin").
- Old repo directories map to one app: `squirrel-admin` → **Admin**, `squirrel-gatsby-sanity` / `…-web` → **Web** (or **Web-next** when the work was in `web-next/`), `squirrel-cms` → **CMS**, and `squirrel-api` sessions from before 2026-10-07 → **API**.
- Side projects keep their own name (`basebook-next`, `techchutes`).

## Step 3 — Extract activity, grouped by calendar day

Bucket findings by the **local** calendar date the work happened — use each JSONL line's `timestamp` field converted to local time, not file mtime, since a session can span midnight (in either timezone).

`.timestamp` is UTC ISO-8601 **with fractional seconds**, which `jq`'s `fromdate` rejects. Strip them, then add `$OFFSET` from Step 1 (e.g. +0700 → 25200):

```bash
LT='((.timestamp|sub("\\.[0-9]+Z$";"Z")|fromdate)+25200|strftime("%Y-%m-%d %H:%M"))'
grep -E '<utc window regex>' "$f" | jq -r "select(.type==\"user\") | $LT + \" | \" + ..."
```

If a jq line silently returns nothing, that's almost always `fromdate` choking on the fractional seconds — check before assuming the day had no activity.

For each file, look for (via `grep`/`jq` — don't read huge files raw):
- `git commit -m` messages
- `git checkout -b` / branch creation
- `git push`, `gh pr create`, PR merges ("Merge pull request", squash-merge mentions)
- Release/version activity (version bumps, tags, changelog entries, "release", "deploy")
- User-stated goals/requests and the assistant's final summary of what was done
- Design/approach discussions that didn't (yet) ship as code — these count as "brainstorm" items

If a session file is large, delegate the parsing to a fresh general-purpose subagent (one per project directory or a batch) rather than reading full transcripts into your own context — mirror the approach used earlier in this conversation. Ask each subagent to return dated, deduplicated bullets per app, explicitly excluding code/file paths.

## Step 4 — Collect pull request events from GitHub

Take PR data (titles, branches, timestamps) from GitHub itself (`gh`, already authenticated), then keep only PRs that the user's Claude sessions worked on.

Repos (all owned by `npertuset`): `squirrel-api` (the monorepo), `techchutes`, `basebook-next`, and, only when the range starts before 2026-10-08, the archived `squirrel-admin`, `squirrel-gatsby-sanity`, `squirrel-cms`. Only the user's own PRs (`--author @me`) unless they ask for everyone's.

For monorepo PRs the **Apps** column comes from the PR's changed files: top-level folders `api`, `admin`, `web`, `web-next`, `cms`, `brain` → `API`, `ADMIN`, `WEB`, `WEB-NEXT`, `CMS`, `BRAIN` (the same tags as the root `CHANGELOG.md`); a PR touching only root files (`.github`, `CHANGELOG.md`, `docs`…) is `REPO`. Old repos map to one app (`squirrel-admin` → `ADMIN`, `squirrel-gatsby-sanity` → `WEB`, `squirrel-cms` → `CMS`); `basebook-next` keeps its name.

An event counts when its timestamp falls inside the UTC window from Step 1:
- **opened** — `createdAt` in the window
- **merged** — `mergedAt` in the window
- **closed** — `closedAt` in the window and the PR was **not** merged (closed without merging)

A PR can have several events in the range (opened one day, merged the next); list it under each day. Same-day events collapse into one row ("opened + merged").

`gh` timestamps have no fractional seconds, so `fromdate` works directly here. Use `$START_UTC`, `$END_UTC`, `$OFFSET` from Step 1:

```bash
# add squirrel-admin squirrel-gatsby-sanity squirrel-cms when the range starts before 2026-10-08
for repo in squirrel-api techchutes basebook-next; do
  gh pr list -R npertuset/$repo --state all --author @me --search "updated:>=<start-1day>" --limit 200 \
    --json number,title,state,isDraft,headRefName,baseRefName,createdAt,closedAt,mergedAt,url,body,files \
  | jq -r --arg repo "$repo" --arg S "$START_UTC" --arg E "$END_UTC" --argjson off "$OFFSET" '
      def inwin($t): $t != null and $t >= $S and $t < $E;
      def lday($t): ($t | fromdate + $off | strftime("%Y-%m-%d"));
      def apps($p):
        if $repo == "squirrel-api" then
          ([$p.files[]?.path | split("/") | select(length > 1) | .[0]
            | select(IN("api","admin","web","web-next","cms","brain")) | ascii_upcase] | unique
           | if length == 0 then "REPO" else join(", ") end)
        else {"squirrel-admin":"ADMIN","squirrel-gatsby-sanity":"WEB","squirrel-cms":"CMS"}[$repo] // $repo end;
      .[] as $p
      | ( [ (if inwin($p.createdAt) then {d: lday($p.createdAt), ev: "opened"} else empty end),
            (if inwin($p.mergedAt) then {d: lday($p.mergedAt), ev: "merged"}
             elif $p.mergedAt == null and inwin($p.closedAt) then {d: lday($p.closedAt), ev: "closed"}
             else empty end) ]
          | group_by(.d)[] )
      | [ .[0].d, $repo, $p.number, (map(.ev) | join(" + ")), $p.headRefName, $p.baseRefName,
          $p.title, $p.isDraft, $p.url, apps($p),
          ([($p.body // "") | scan("https://app\\.clickup\\.com/t/[A-Za-z0-9/]+")] | unique | join(" ")) ] | @tsv'
done | sort -r > /tmp/squirrel-pr-events.tsv
```

### Keep only PRs from the user's sessions

A PR counts as session-related if its PR URL path (`<repo>/pull/<number>`) **or** its head branch name appears in a squirrel transcript line inside the UTC window. Use the same files and window regex as Steps 2–3, so a PR merged in the GitHub UI on a day with no session touching it is left out, which is intended.

```bash
# In-window transcript lines from the Step 2 file list, once.
# Project dir names start with "-", so pass `--` (or use absolute paths) or grep reads them as options
# and the file comes out empty, which silently drops every PR.
grep -hE '<utc window regex>' -- <step 2 files> > /tmp/squirrel-window.txt

while IFS=$'\t' read -r day repo num ev head base title draft url apps clickup; do
  if grep -qF "$repo/pull/$num" /tmp/squirrel-window.txt || grep -qF "$head" /tmp/squirrel-window.txt; then
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$day" "$repo" "$num" "$ev" "$head" "$base" "$title" "$draft" "$url" "$apps" "$clickup"
  fi
done < /tmp/squirrel-pr-events.tsv
```

If `gh` fails (auth, network), say so in the PR section instead of silently leaving it empty.

## Step 5 — Output format

The report has **two sections**, in this order. Date headings in both are **local** dates, newest first.

### Section 1 — Activity

Group strictly **by date (newest first), then by app (alphabetical) within each date**. Skip an app entirely for a given date if it had no meaningful activity that day — don't print empty "no activity" bullets except when the whole range had nothing at all (then note it once).

List each piece of work (a feature, fix, release, or brainstorm) as its own bullet, and write **every bullet as exactly one short sentence**: the outcome verb (Shipped, Fixed, Opened a PR for, Reverted, Brainstormed…) plus what the work is, and nothing else. Leave out how it got there: review rounds, QA runs, prototypes, test environments, who picked what. No trailing period. Don't merge separate pieces of work into one bullet, and don't spread one piece over several bullets. No code snippets, no raw branch names unless the name itself is the clearest description of the work.

- ✅ `Shipped the jacket and pants size for Sumo on the item page`
- ❌ `Shipped the jacket and pants size for Sumo on the item page, which the review bot passed in one round.`
- ✅ `Shipped priority markers on the Orders page (API + Admin): a pill after the order summary and a row highlight`
- ❌ `Shipped priority markers on the Orders page (API + Admin): a pill after the order summary and a row highlight, picked from a prototype of options.`

**Releases get their entries as children.** A release bullet (`Released 4.96.0 to production`) lists every changelog entry of that release as nested bullets under it, in changelog order, including entries from other people's PRs. Take them from the `## [<version>]` section of the root `CHANGELOG.md` on `main` (`gh api repos/npertuset/squirrel-api/contents/CHANGELOG.md -H "Accept: application/vnd.github.raw"`); for archived repos, which may have no root changelog, use the release PR's body (`gh pr view <n> -R npertuset/<repo> --json body`). Each child keeps the entry's app tags (`[API][ADMIN]`) and its wording, drops the PR link, has no trailing period, and is cut to its first sentence when the entry is longer (older, pre-4.77.0-style entries). A release with an empty section gets one child: `No changelog entries`.

### Section 2 — Pull requests

From Step 4. One table per date, rows sorted by apps then PR number. Branch names **are** shown here (unlike Section 1), since where a PR came from and merged into is the point.

- **Status**: `Opened`, `Merged`, `Closed (not merged)`, or combined (`Opened + merged`). Add `(draft)` to opened drafts.
- **Branch → base**: the head branch and the branch it targets / was merged into. Call out a base that isn't `main` (e.g. `deploy/production` for releases, or a feature branch for stacked PRs) — that's the useful detail.
- **Apps**: from Step 4 (`API, ADMIN`, `WEB`, `REPO`…).
- **PR**: `[#123](url)` link; prefix the repo for anything outside the monorepo (`basebook-next#12`, or an archived repo for older ranges).
- **ClickUp**: the ClickUp task link(s) from the PR description, shown as `[<task id>](url)` (the last path segment, e.g. `86bcbre7z`). Several tasks → list them all, comma-separated. None → `—`.

If the range had no PR events, write "No PRs opened, merged, or closed." once.

```
# Activity

## YYYY-MM-DD

**Admin**
- Shipped the email-template preview with the real subject and body for each trigger
- Fixed the voucher list pagination skipping the last page

**API**
- Brainstormed a retry queue for failed webhook deliveries

**Repo**
- Released 4.96.0 to production
  - [API][ADMIN] Mark orders with priority items on the Orders page with HIGH / MEDIUM / LOW pills and a row highlight
  - [API] Fix setting an item's Priority back to "None", which failed to save
  - [ADMIN] Show Sumo jacket and pants sizes on the new item page

## YYYY-MM-DD

**Web**
- Started the checkout address-form rework

# Pull requests

## YYYY-MM-DD

| Apps | PR | Title | Branch → base | Status | ClickUp |
|---|---|---|---|---|---|
| ADMIN | [#1902](url) | Show real subject and body per trigger on email templates page | `feat/email-template-preview-adjustment` → `main` | Opened + merged | [86bcbre7z](url) |
| API, ADMIN, WEB | [#1925](url) | Release/4.96.0 | `release/4.96.0` → `deploy/production` | Merged | — |

## YYYY-MM-DD

| Apps | PR | Title | Branch → base | Status | ClickUp |
|---|---|---|---|---|---|
| … | … | … | … | … | … |
```
