---
name: full-stop
description: Trigger this if the user says 'full stop', even as a closing "Full stop." that reads like emphasis. Same as full-send but stops with the PR ready for the user to merge. Never merges.
---

# Full Stop

Do the same work as `full-send`, but stop with the PR ready for the user to
merge. Never merge it.

Read [full-send](../full-send/SKILL.md) and follow its steps 1 to 8 (tracker,
change, proof, docs, council, PR, babysit, change report), its proof rules,
and its rules for asking the user. An explicit "full stop" request authorizes
that work without a separate "full send" request, including the testing
permission and the worktree work. Its merge permission and its wrap-up step
do not apply. The overrides below take precedence.

This is the default for any repo where the user merges by hand (Squirrel
monorepo PRs, by their rules), and for any thread where the user said they
want to look or try it first.

## No merging

You may commit, push, rebase, fix conflicts, and use `--force-with-lease` on
this task's branch. Never merge, enable auto-merge, enter a merge queue, push
to the default branch, bypass branch protection, or delegate those actions.

Disable existing auto-merge and remove the PR from any merge queue before
work begins; check again before each push. Report these changes. If you
cannot prevent automatic merging, report the blocker before proceeding.

## Stop at the gate

Use full-send's merge gate as the readiness check. Replace its merge,
wrap-up and final report steps with a handoff. Proof, council and the bot's
review must cover the final diff; recheck behaviour changes and meaningful
conflict fixes before handoff.

Fetch the target branch and check the live PR's head, base, checks, reviews,
and mergeability. Confirm it is open, not a draft, and not set to merge
without the user. If someone else merged it, report that instead, and offer
`wrap-up`.

- **Ready to merge:** the merge gate passes. Leave the PR open and unmerged.
  Heading `# ✅ GOOD TO MERGE`.
- **Waiting for required approval:** only human approval remains. Confirm
  that this is the actual blocker. Heading `# ⏳ WAITING FOR REVIEW`.
- **Needs a decision:** a finding that contradicts a Decision and you are not
  sure the decision stands, a repeated point, the round budget. Ask with
  `AskUserQuestion`; heading `# ⚠️ NEEDS YOUR DECISION`.
- **Blocked:** explain what prevents readiness, what you tried, and what is
  needed. Heading `# ❌ BLOCKED`.

In T3 Code, call `unwatch_pull_request` before the handoff or a question.

## Handoff message

The heading, then the PR on the next line (`<repo>#<n> — <url>`), then:
final head, verdict, proof, council scores, bot rounds and outcome, declined
findings with reasons, decisions made for the user, follow-ups, the change
report's absolute path, and the ClickUp link to paste if the user still has
to send it. State that the PR is still open and unmerged, that the worktree
and `.fullsend/` are kept, and that `wrap-up` cleans them after the merge.
