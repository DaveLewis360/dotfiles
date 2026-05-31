# dotfiles

Personal Hyprland + **Caelestia** desktop configuration (Arch Linux).

This repo holds the *configuration & theming layer*. The Caelestia **shell program**
itself lives in a separate fork (see below).

## Active layout

| Component | Symlink | Source |
|---|---|---|
| Hyprland | `~/.config/hypr` | `dotfiles/hypr` |
| Caelestia shell **config** | `~/.config/caelestia` | `dotfiles/shell` |
| Ghostty | `~/.config/ghostty/config` | `dotfiles/apps/ghostty/config` |
| pywal | `~/.config/wal` | `dotfiles/.config/wal` |
| waypaper / xsettingsd / wallust / vim | `~/.config/*` | `dotfiles/.config/*` |
| Xresources | `~/.Xresources` | `dotfiles/.Xresources` |

> The Caelestia **shell program** (the running QML) is a separate repository:
> `~/.config/quickshell/caelestia` → `~/Reference/my-caelestia-shell`
> (fork of `caelestia-dots/shell`, with local customizations). `install.sh` does
> **not** touch it.

## Install

```bash
git clone <this-repo> ~/dotfiles
cd ~/dotfiles
./install.sh   # idempotent; only creates/refreshes symlinks, never overwrites real files
```

## Structure

- `hypr/` — Hyprland config (core, appearance, scripts, wallpapers)
- `shell/` — Caelestia shell config (`shell.json`, `cli.json`, user overrides)
- `apps/` — per-app configs (ghostty, vesktop, zen)
- `scripts/` — helper scripts
- `.config/` — additional XDG configs (ML4W-derived: waypaper, wallust, vim, …)

## Notes

- Generated caches, browser-profile data and large media (`*.mp4`, …) are
  git-ignored on purpose (see `.gitignore`) — they stay on disk but are not versioned.
- Related repos on this machine: `Reference/caelestia-shell` (pristine upstream),
  `Reference/my-caelestia-shell` (active fork), `Archivum/.dotfiles` (holman framework,
  source of `~/.gitconfig`, `~/.vimrc`, …).
