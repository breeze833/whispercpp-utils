# My Whisper.cpp STT Related Utilities

I would like to use whisper.cpp as the speech-to-text engine on RPi4.
Usually I mix Chinese and English. Therefore, the default startup options
require special tweaks.

In this project, I collect my experimental scripts and utility programs.

## Build Whisper.cpp

### Without GPU, With BLAS

```
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp
cmake -B build -DGGML_BLAS=1
cmake --build build -j --config Release
```

## Download Models

It requires at least the small model for resolving the mixture of Chinese and English properly.
The VAD is the useful preprocessing model (though may introduce overhead) for reducing the actual processing size.
The RPi4 ARM NEON architecture is highly optimized for 4-bit mathematical lookups.
Therefore, we need to manually convert the model to `q4_0` to get hardware support.

```
./models/download_ggml_model.sh small
./models/download_vad_model.sh silero-v6.2.0
./build/bin/whisper-quantize ./models/ggml-small.bin ./models/ggml-small-q4_0.bin q4_0

```

## Files

* `scripts/` contains shell scripts
  * `whispercpp-start.sh` starts the `whisper-server` with some default options
  * `transcribe.sh` uses `curl` to send the WAV file to the server and gets the JSON response
  * `normalize_wav.sh` uses `ffmpeg` to convert the input audio file to the WAV format that can be consumed by `whisper-server` (16kHz Mono S16LE)
  * `record_wav.sh` uses `arecord` to capture audio from the default device and save to the WAV file
* `systemd/` contains the service files
  * `whisper-server.service` starts the whisper.cpp service
  * `vad-stt.service` starts the `vad-stt` program to transcribe speech and inject via HID
* `vad_stt` contains the python utility to transcribe and inject via HID


