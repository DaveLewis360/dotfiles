#!/usr/bin/env bash
# Idempotent symlink installer for ~/dotfiles.
# Safe: only creates/refreshes symlinks; never overwrites a real file/dir.
set -euo pipefail
DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

link() { # $1 = path inside repo, $2 = target on system
  local src="$DOTFILES/$1" dst="$2"
  [ -e "$src" ] || { echo "skip (no source): $1"; return; }
  mkdir -p "$(dirname "$dst")"
  if [ -L "$dst" ] || [ ! -e "$dst" ]; then
    ln -sfn "$src" "$dst"; echo "linked:  $dst -> $src"
  else
    echo "SKIP (real file exists, not touching): $dst"
  fi
}

link hypr                "$HOME/.config/hypr"
link shell               "$HOME/.config/caelestia"
link .config/wal         "$HOME/.config/wal"
link .config/waypaper    "$HOME/.config/waypaper"
link .config/xsettingsd  "$HOME/.config/xsettingsd"
link .config/wallust     "$HOME/.config/wallust"
link .config/vim         "$HOME/.config/vim"
link apps/ghostty/config "$HOME/.config/ghostty/config"
link .Xresources         "$HOME/.Xresources"

echo
echo "Done. NOTE: the Caelestia *shell program* is a separate repo:"
echo "  ~/.config/quickshell/caelestia -> ~/Reference/my-caelestia-shell"
echo "This installer intentionally does NOT touch it."
