---
name: leaving-pr-comments
description: Use whenever leaving comments on GitHub on the user's behalf (replies to review findings, decline notes, status comments).
---

# Leaving PR Comments

Prefix every agent-authored comment left on the user's behalf with this GitHub
note callout:

```md
> [!NOTE]
> 🤖 **<model> responding on behalf of <user>**

Actual comment starts here.
```

Use the verified public name of the model that wrote the comment, and the
user's GitHub login (`gh api user --jq .login`).

If the harness does not expose a model name, use the harness name. Do not
guess.

Before posting, check the entire comment, including quoted text and
attachments, for secrets and private details.

Keep the attribution inside the note and the actual reply outside it. The
context line must start with the robot emoji. Do not add a horizontal rule,
Setext underline, heading, signature footer, or a second attribution.

## Squirrel repos (`npertuset/*`)

- Commands to the review bot are **not** comments on the user's behalf. A
  command (`@squirrel-agent review`, `review loop`, …) is a comment of its
  own with nothing else in it, and gets no note callout. A command inside a
  quote or code block is ignored by the bot, so never quote one in a reply
  you want it to run.
- Never write `@agent`. It notifies the owner of the bot's GitHub account.
  The bot is `@squirrel-agent`.
- Declining a finding because of a recorded decision: quote the decision and
  its date from `.fullsend/TODO.md` (or the thread), say it stands, and ask
  the bot not to raise it again. Then resolve the thread.

## Decline template

```md
> [!NOTE]
> 🤖 **<model> responding on behalf of <user>**

Not changing this. <One sentence why: out of scope / decided on <date>: "<decision>" / rare case, listed as a follow-up.>
```
