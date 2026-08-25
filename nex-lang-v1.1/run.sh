#!/bin/bash
if [ $# -eq 0 ]; then
    echo "Usage: ./run.sh [file.N or file.nex]"
    exit 1
fi
python3 interpreter.py "$@"
