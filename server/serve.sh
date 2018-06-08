#!/bin/sh

if [[ "$1" == "bhsa" ]]; then
    python3 bhsa.py &
    python3 index.py
elif [[ "$1" == "web" ]]; then
    python3 index.py
elif [[ "$1" == "cunei" ]]; then
    echo "not yet implemented"
fi

