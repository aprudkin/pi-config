#!/bin/zsh
# Commit and push non-ignored changes in the Pi configuration repository.
# Invoked by the com.aprudkin.pi-agent-autopush LaunchAgent every 30 seconds.

set -u

REPO="$HOME/.pi/agent"
LOG_DIR="$HOME/Library/Logs"
LOG_FILE="$LOG_DIR/pi-agent-autopush.log"
LOCK_DIR="${TMPDIR:-/tmp}/pi-agent-autopush.lock"

mkdir -p "$LOG_DIR"

# Do not run overlapping syncs.
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  exit 0
fi
trap 'rmdir "$LOCK_DIR"' EXIT

cd "$REPO" || {
  print -r -- "$(date '+%Y-%m-%d %H:%M:%S') cannot enter $REPO" >> "$LOG_FILE"
  exit 1
}

# Include staged, unstaged and non-ignored untracked files, but do nothing
# when the repository is already clean. Ignored secrets/runtime files stay out.
if git diff --quiet && git diff --cached --quiet && [[ -z "$(git ls-files --others --exclude-standard)" ]]; then
  exit 0
fi

git add -A || {
  print -r -- "$(date '+%Y-%m-%d %H:%M:%S') git add failed" >> "$LOG_FILE"
  exit 1
}

if git diff --cached --quiet; then
  exit 0
fi

git commit -m "chore: sync Pi agent configuration" >> "$LOG_FILE" 2>&1 || {
  print -r -- "$(date '+%Y-%m-%d %H:%M:%S') git commit failed" >> "$LOG_FILE"
  exit 1
}

git push origin main >> "$LOG_FILE" 2>&1 || {
  print -r -- "$(date '+%Y-%m-%d %H:%M:%S') git push failed; will retry on the next run" >> "$LOG_FILE"
  exit 1
}

print -r -- "$(date '+%Y-%m-%d %H:%M:%S') synced Pi agent configuration" >> "$LOG_FILE"
