#!/bin/bash
if [[ $# -eq 0 ]]; then
    echo $0 \<input.wav\>
    exit 1;
fi
curl http://127.0.0.1:8080/inference -H "Content-Type: multipart/form-data" -F "file=@$1" -F "response_format=jsonf" -F "temperature=0.0"
