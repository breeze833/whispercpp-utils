# My Whisper.cpp STT Realted Utilities

I would like to use whisper.cpp as the speech-to-text engine.
Usually I mix Chinese and English. Therefore, the default startup options
require special tweaks.

In this project, I collect my experimental scripts and utility programs.

## Build Whisper.cpp

### Without GPU, With BLAS

```
cmake -B build -DGGML_BLAS=1
cmake --build build -j --config Release
```

## Download Models

It requires at least the small model for resolving the mixture of Chinese and English properly.
The VAD is the useful preprocessing model for reducing the actual processing size.

```
cd models
./download_ggml_model.sh large-v3-turbo-q8_0
./download_vad_model.sh silero-v6.2.0

```

## Files

* `scripts/` contains shell scripts
  * `whispercpp-start.sh` starts the `whisper-server` with some default options
  * `transcribe.sh` uses `curl` to send the WAV file to the server and gets the JSON response
  * `normalize_wav.sh` uses `ffmpeg` to convert the input audio file to the WAV format that can be consumed by `whisper-server`
* `systemd/` contains the service files
  * `whisper-server.service` starts the whisper.cpp service

