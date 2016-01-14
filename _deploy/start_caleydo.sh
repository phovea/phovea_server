#!/usr/bin/env bash

chmod +x plugin_scripts.sh
sleep 1
./plugin_scripts.sh pre_start
sleep 1
./gunicorn_start.sh
