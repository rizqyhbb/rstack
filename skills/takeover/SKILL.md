---
name: takeover
description: Take over existing work. Use when the user asks to take over a PR, branch, or agent thread, or requests a takeover.
---

# Takeover

Take responsibility for finishing the original goal while preserving the
original contributors' credit. Do not defend an implementation just because
another agent already built it.

Read the source PR, branch, or thread, including review findings and the user's
later corrections. Resolve the handoff to the actual code and current head,
and account for uncommitted work. Treat the handoff as context, not proof.

For a replacement PR, import the original commits onto a new branch and add
your fixes separately. Honor an explicitly requested in-place or stacked
continuation instead. Do not overwrite unrelated work or change the original
PR without authorization.

Preserve Git authorship and existing co-author trailers. Credit the original
contributors in the PR description and link the original PR when there is one.
If the work will be squashed, preserve human author/co-author credit in the
merge commit too, using verified identities rather than guessed emails. Model
attribution is not a substitute for contributor credit.

Use `modernize` to update the continuation against its intended base and
current architecture. Rework what is necessary to finish the same goal, not
unrelated features. Simplify the implementation without dropping intended
behavior or surfaces. Recheck the source PR too: it may have improved while
you were working.

Independently verify the original failure and realistic workflows, following
repository guidance and permissions. Green mocked tests do not prove the user
experience works. State what remains unverified.

When the requested finish includes a PR, use `file-pr` to file or update it,
then `babysit-pr` rather than stopping at creation. Use `leaving-pr-comments`
for replies. Merge or close the original PR only when authorized.

Report what you inherited, what you changed, how you verified it, how credit
was preserved, and any remaining decision.

## rstack notes

- **A T3 Code thread as the source:** read it with `t3_thread_read` (its
  link or id), including the questions the user answered and later
  corrections. Its worktree is `~/.t3/worktrees/<repo>/<branch>`; the
  Squirrel ones are under `~/Documents/project/squirrel/wt/<feature>/`.
  Uncommitted work there is user-owned: commit it on the branch as a WIP
  commit before anything else, never stash.
- **Rebuild the tracker.** Write `.fullsend/TODO.md` from the thread: Goal,
  Out of scope, and every Decision with the date it was made, before
  changing code. A decision made in the old thread stands.
- **Continuing in place** (the user said "take over" without "new PR"):
  work on the same branch and PR, and then run `full-stop` from its step 2,
  or `full-send` if the user asked to merge.
- Squirrel repos: the review bot is `@squirrel-agent`, never `@agent`.
