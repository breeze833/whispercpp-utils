#!/bin/bash
WHISPER_DIR=~/programs/src/whisper.cpp/build
MODEL_DIR=$WHISPER_DIR/../models
${WHISPER_DIR}/bin/whisper-server -m ${MODEL_DIR}/ggml-large-v3-turbo-q8_0.bin --vad -vm ${MODEL_DIR}/ggml-silero-v6.2.0.bin -vt 0.3 -l zh --prompt "輸出台灣繁體中文，包含正確標點符號。例如：逗號、頓號、句號。" --carry-initial-prompt $@
