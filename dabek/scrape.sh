#!/bin/sh
set -eu

curl --fail -o dabek.html --compressed -\# -A '' "http://autobusy-dabek.pl/rozklad-jazdy/"
