#!/bin/bash
if [[ $# -eq 0 ]]; then
    echo $0 \<output.wav\>
    exit 1;
fi
arecord -r 16000 -c 1 -f S16_LE $1
