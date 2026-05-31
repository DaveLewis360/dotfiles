#!/usr/bin/env sh

if [ "$1" = '-g' ]; then
    group=1
    shift
fi

if [ $# -ne 2 ]; then
    echo 'Wrong number of arguments. Usage: ./wsaction.fish [-g] <dispatcher> <workspace>'
    exit 1
fi

active_ws=$(hyprctl activeworkspace -j | awk -F'"id":' '{print int($2); exit}')

if [ -n "$group" ]; then
    target=$(( ($2 - 1) * 10 + active_ws % 10 ))
else
    target=$(( (active_ws - 1) / 10 * 10 + $2 ))
fi

hyprctl dispatch "$1" "$target"
