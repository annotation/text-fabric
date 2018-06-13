#!/bin/sh

python3 serveTf.py "$1" &
PID_SERVE_TF=$!

python3 index.py "$1"

echo "Terminated web server"

kill $PID_SERVE_TF

echo "Terminated TF-data server"
