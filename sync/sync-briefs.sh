#!/bin/zsh
#
# Pulls the markdown brief archive down from GitHub to local disk.
# Deliberately contains no AI and no API calls — the cloud routine has already
# written and committed the brief, so all this needs to do is fast-forward.
#
# Driven by sync/com.nate.daily-brief-sync.plist (7:20am local). launchd re-fires
# missed StartCalendarInterval jobs when the Mac wakes, so a closed lid at 7:20
# means a late pull, not a lost one.

set -uo pipefail

REPO="/Users/nathananderson/Claude Workflows/daily-brief"
LOG="$REPO/sync/sync.log"
GIT=/opt/homebrew/bin/git

export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Keep the log from growing without bound (trim to last 500 lines over ~200KB).
if [[ -f "$LOG" ]] && [[ $(stat -f%z "$LOG") -gt 200000 ]]; then
  tail -n 500 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

exec >> "$LOG" 2>&1
echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') sync start ==="

cd "$REPO" || { echo "FAIL: repo dir missing"; exit 1; }

before=$(ls -1 briefs/*.md 2>/dev/null | wc -l | tr -d ' ')

if ! "$GIT" pull --ff-only --no-rebase origin main; then
  echo "FAIL: git pull failed (diverged history, or no network). Local changes are untouched."
  exit 1
fi

after=$(ls -1 briefs/*.md 2>/dev/null | wc -l | tr -d ' ')
newest=$(ls -1 briefs/*.md 2>/dev/null | tail -1)

echo "briefs: $before -> $after   newest: ${newest:-none}"
echo "=== sync done ==="
