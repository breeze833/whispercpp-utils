#!/bin/bash
cd ${WHISPER_DIR:=~/src/whisper.cpp}
./build/bin/whisper-server -m ./models/ggml-small-q4_0.bin --vad -vm ./models/ggml-silero-v6.2.0.bin -vt 0.3 -l zh --prompt "輸出台灣繁體中文，包含正確標點符號。例如：逗號、頓號、句號。" --carry-initial-prompt $@
