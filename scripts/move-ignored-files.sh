#!/usr/bin/env bash
# One-time helper for clones made before the bots moved into bot/ and the website into
# website/ (e.g. the Docker host). `git pull` moves tracked files, but gitignored ones
# (.env, locale.json, data/rotation.db, .venv, ...) stay behind in the old folders.
# This moves whatever is left into the new folders. It never overwrites a file.
#
# Usage: scripts/move-ignored-files.sh [--dry-run]

set -euo pipefail
shopt -s dotglob nullglob
cd "$(dirname "$0")/.."

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

MOVES=(
  "game-night-bot:bot/game-night-bot"
  "music-bot:bot/music-bot"
  "twitch-bot:bot/twitch-bot"
  "voice-chat-bot:bot/voice-chat-bot"
  "game-night-website:website/game-night-website"
)

run() {
  if ((DRY_RUN)); then echo "  would run: $*"; else "$@"; fi
}

# Move src/* into dst/, descending into folders that exist on both sides (like data/).
merge() {
  local src=$1 dst=$2 entry name
  for entry in "$src"/*; do
    name=${entry##*/}
    if [[ ! -e "$dst/$name" && ! -L "$dst/$name" ]]; then
      echo "  $entry -> $dst/$name"
      run mv "$entry" "$dst/$name"
    elif [[ -d "$entry" && ! -L "$entry" && -d "$dst/$name" ]]; then
      merge "$entry" "$dst/$name"
    else
      echo "  skipped, already exists: $dst/$name"
    fi
  done
}

found=0
for pair in "${MOVES[@]}"; do
  old=${pair%%:*}
  new=${pair#*:}
  [[ -d "$old" ]] || continue
  found=1
  echo "$old/ -> $new/"
  run mkdir -p "$new"
  merge "$old" "$new"
  if ((!DRY_RUN)); then
    find "$old" -depth -type d -empty -delete
    if [[ -d "$old" ]]; then
      echo "  left in $old/ (nothing was overwritten; sort these out by hand):"
      find "$old" -mindepth 1 | sed 's/^/    /'
    fi
  fi
done

if ((!found)); then
  echo "Nothing to move: the old folders are already gone."
  exit 0
fi

((DRY_RUN)) && exit 0
cat <<'MSG'

Done. Next:
  - Start each bot from its new folder, e.g. cd bot/music-bot && docker compose up -d
    (container names are unchanged).
  - A moved Python .venv has stale paths: delete it and re-create it (e.g. uv sync).
MSG
