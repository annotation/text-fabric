#!/bin/sh

python3 serveTf.py "$1" &
PID_SERVE_TF=$!

python3 index.py "$1"

kill $PID_SERVE_TF
