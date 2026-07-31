# A PATH és a QML_IMPORT_PATH is duplikálódott, ugyanabból az okból: több fájl
# fűzött hozzájuk feltétel nélkül. A ~/.local/bin három külön helyen kerül be —
# .zprofile egyszer hozzáfűzi, négy sorral lejjebb elé is fűzi, a .zshrc pedig
# még egyszer —, így négy példányban szerepelt. A zsh `path` tömbjét egyedire
# állítva mindhárom hozzáadás egybe olvad, és nem kell egyik sort sem törölni:
# azok a .zshrc-ben és .zprofile-ban maradhatnak biztonsági hálóként a nem-login
# interaktív shellekhez. Ez a fájl minden zsh-indításnál elsőként fut, ezért itt
# a helye.
typeset -U path PATH

# QML import path for the active dotfiles profile.
#
# The value is written by dotswitch to ~/.local/state/dotfiles/qml_import_path.
# Nothing regenerates this file, despite what the previous comment claimed — it
# is hand-maintained, so edit it here.
#
# .zshenv is sourced for EVERY zsh invocation, including non-interactive
# subshells, so this block has to be idempotent. The previous version prepended
# unconditionally:
#
#     export QML_IMPORT_PATH="$(cat "$_qml_path_file"):${QML_IMPORT_PATH:-}"
#
# which appended one more copy of the same directory per nesting level (three
# copies were observed in a live session) and left a trailing colon whenever the
# variable started out empty — a trailing colon is an empty path element, which
# some Qt versions read as the current directory.
#
# Tying the variable to an array marked unique (typeset -U) both prepends the
# active profile's path and collapses any duplicates already inherited from the
# environment, so a polluted value repairs itself.
_qml_path_file="$HOME/.local/state/dotfiles/qml_import_path"
if [[ -r "$_qml_path_file" ]]; then
    _qml_path="$(<"$_qml_path_file")"
    if [[ -n "$_qml_path" ]]; then
        typeset -T QML_IMPORT_PATH qml_import_path :
        typeset -U qml_import_path
        qml_import_path=("$_qml_path" $qml_import_path)
        qml_import_path=(${(@)qml_import_path:#})
        export QML_IMPORT_PATH
    fi
    unset _qml_path
fi
unset _qml_path_file

# No hardcoded fallback on purpose. The previous version fell back to the
# my-caelestia fork's build directory whenever the state file was missing, which
# injected that one profile's QML modules even when a different profile was
# active. If the state file is absent, dotswitch has not run yet and it should
# set the path itself.

export BROWSER=zen-browser
