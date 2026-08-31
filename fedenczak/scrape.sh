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
 $baseurl/komunikacja-miejska/

 $baseurl/nowogard-golenow-szczecin/
 $baseurl/resko-szczecin/
 $baseurl/goleniow-goleczewo/
 $baseurl/maszewko-goleniow/

 $baseurl/radowo-wiekie-nowogard/
 $baseurl/adowo-wielkie-lobez/
 $baseurl/lobez-gryfice/
 $baseurl/szkolny-nowogard-maszewo/

 $baseurl/nowogard-resko/
 $baseurl/stargard-nowogard/
 $baseurl/szkolny-nowogard-goleczewo/
)

curl --fail --remote-name-all --output-dir html/ --compressed -\# --rate 1/4s -A '' "${files[@]}"
