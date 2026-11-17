#!/usr/bin/env bash
# Poll a PR until @squirrel-agent posts a review newer than the trigger comment.
# Usage: poll-review.sh <owner/repo> <pr> <trigger-comment-id> <trigger-created-at> [interval-sec] [timeout-min]
# Exit: 0 = review posted, 2 = timeout, 1 = error.
set -euo pipefail

repo=$1 pr=$2 trigger_id=$3 since=$4
interval=${5:-420} timeout=${6:-90}
marker='<!-- squirrel-agent:review -->'
deadline=$(( $(date +%s) + timeout * 60 ))
warned_no_eyes=0

while :; do
  sleep "$interval"

  id=$(gh api --paginate "repos/$repo/issues/$pr/comments?since=$since" \
    --jq ".[] | select(.created_at > \"$since\" and (.body | contains(\"$marker\"))) | .id" | tail -1)
  if [ -n "$id" ]; then
    echo "REVIEW_POSTED comment_id=$id"
    exit 0
  fi

  if [ "$warned_no_eyes" -eq 0 ]; then
    eyes=$(gh api "repos/$repo/issues/comments/$trigger_id" --jq '.reactions.eyes')
    if [ "$eyes" = "0" ]; then
      echo "WARN no 👀 reaction on trigger comment yet — review agent may not have picked it up"
    fi
    warned_no_eyes=1
  fi

  if [ "$(date +%s)" -ge "$deadline" ]; then
    echo "TIMEOUT no squirrel-agent review after ${timeout}m"
    exit 2
  fi
  echo "$(date -u +%H:%M:%SZ) still waiting for squirrel-agent review on $repo#$pr"
done
