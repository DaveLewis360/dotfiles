#!/bin/bash
CLASS=$1
PROFILE=$2
URL=$3

# Ellenőrizzük, hogy fut-e már az adott osztályú ablak a Hyprlandben
if hyprctl clients -j | jq -e ".[] | select(.class == \"$CLASS\")" > /dev/null; then
    # Ha fut, akkor csak fókuszálunk rá. 
    # Mivel special workspace-en van, a Hyprland automatikusan felugrasztja.
    hyprctl dispatch focuswindow "class:^($CLASS)$"
else
    # Ha nem fut, elindítjuk a Zent a megfelelő profillal
    zen-browser --new-instance --name "$CLASS" --class "$CLASS" -P "$PROFILE" "$URL"
fi
