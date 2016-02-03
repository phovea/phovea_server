#!/usr/bin/env bash

chmod +x plugin_scripts.sh
sleep 1

function isRedHat {
  [ -f /etc/redhat-release ]
}

if isRedHat ; then
  ./plugin_scripts.sh pre_start_redhat
else:
  ./plugin_scripts.sh pre_start
fi

sleep 1
./gunicorn_start.sh
