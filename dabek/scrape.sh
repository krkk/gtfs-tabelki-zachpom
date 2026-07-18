#!/bin/sh
set -eu

out=rozklad-jazdy.html
if test -f "$out"; then
    newoldname="rozklad-jazdy-$(date +%F --date @$(stat -c %Y "$out")).html"
    echo "$out exists. Rotating it to $newoldname"
    mv "$out" "$newoldname"
fi

curl --fail -o "$out" --compressed -\# -A '' "http://autobusy-dabek.pl/rozklad-jazdy/"
