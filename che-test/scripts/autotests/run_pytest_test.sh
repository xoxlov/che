#!/usr/bin/env bash

cd /var/www/che-test/scripts/autotests
. ./venvpython3/bin/activate
xvfb-run --server-args="-screen 0, 1920x1080x24" pytest ./test/*
deactivate
