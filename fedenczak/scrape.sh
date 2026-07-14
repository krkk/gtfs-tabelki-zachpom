#!/bin/bash
set -euo pipefail

if test -d html; then
    dirname=$(date +%F --date @$(stat -c %Y html/))
    echo "html/ exists. Rotating it to $dirname"
    mv -T html "html_$dirname"
fi

mkdir html
baseurl=https://fedenczak.com.pl
files=(
 $baseurl/adowo-wielkie-lobez/
 $baseurl/goleniow-goleczewo/
 $baseurl/komunikacja-miejska/
 $baseurl/lobez-gryfice/
 $baseurl/maszewko-goleniow/
 $baseurl/nowogard-golenow-szczecin/
 $baseurl/nowogard-resko/
 $baseurl/radowo-wiekie-nowogard/
 $baseurl/resko-szczecin/
 $baseurl/stargard-nowogard/
 $baseurl/szkolny-nowogard-goleczewo/
 $baseurl/szkolny-nowogard-maszewo/
)

curl --fail --remote-name-all --output-dir html/ --compressed -\# --rate 1/4s -A '' "${files[@]}"
