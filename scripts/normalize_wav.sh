#!/bin/bash
if [[ $# -lt 2 ]]; then
    echo $0 \<input audio\> \<output.wav\>
    exit 1;
fi
ffmpeg -i "$1" -ar 16000 -ac 1 -c:a pcm_s16le "$2"
