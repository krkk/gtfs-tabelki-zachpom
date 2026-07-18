#!/bin/sh
set -eu

out=gmina-kobylanka.html
if test -f "$out"; then
    newoldname="gmina-kobylanka-$(date +%F --date @$(stat -c %Y "$out")).html"
    echo "$out exists. Rotating it to $newoldname"
    mv "$out" "$newoldname"
fi

curl --fail -o "$out" --compressed -\# -A '' "https://669ad45b86be9.site123.me/rozk%C5%82ady/komunikacja-gminy-kobylanka"
