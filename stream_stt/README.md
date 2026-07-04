# Streaming STT Processor

The STT program that reads audio streams, chunks them (optionally using WebRTC VAD or fixed-duration chunks for Native/Server-side VAD), transcribes them using whisper.cpp, and sends the output.

Its processing flow is:

1. Reads input speech stream (microphone, file, or standard input)
2. Creates audio fragments (using local WebRTC VAD or fixed-duration intervals)
3. Sends each fragment to `whisper-server` for transcription (which can use native Silero VAD)
4. Sends the transcribed results to the output destination (socket or stdout).

The input could be a WAV file, standard input, or the microphone.
The output could be a unix socket or `stdout`.

## Build

```
sudo apt update
sudo apt install python3-dev portaudio19-dev
python -m venv .venv
.venv/bin/pip install --upgrade pip setuptools
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
```

## Use

### Configure the Audio Device

To enable audio input in the user service, here are some configurations to do
* An audio input device (e.g., USB microphone)
* Configure to enable the audio device in Linux
  * The device should support the exact 16kHz, mono, and S16_LE input format
  * ALSA support automatic conversion if you enable it
  * A sound server may be required to do the software conversion on-the-fly
* Add user `dietpi` to group `audio`

### CLI

Default behavior is to read input from microphone and send output to `/tmp/hid-keyboard.sock`.

```
.venv/bin/stream-stt
```

If you would like to override the configuration, use environment variables:

* `VAD_INPUT` (or `STREAM_INPUT`) for reading the audio data
  * `mic`: read PCM data from the microphone (the default)
  * file name: read WAV data from the file
  * `-`: read the WAV data from the standard input 
* `STT_OUTPUT` (or `STREAM_OUTPUT`) for writing the null-terminated strings (the format is for integrating with my [rpi-hid-keyboard](https://github.com/breeze833/rpi-hid-keyboard) project)
  * `/tmp/hid_keyboard.sock`: the default unix socket name
  * socket name: the specific unix socket name
  * `-`: dump the results to the standard output
* `STT_MODE` (or `VAD_MODE`) to toggle VAD chunking strategy
  * `webrtc` (default): use client-side WebRTC VAD to isolate voice segments.
  * `native`: bypass client WebRTC VAD and chunk audio at regular intervals, letting the `whisper-server`'s native Silero VAD handle speech segment detection.
* `CHUNK_DURATION_S` (only applicable when `STT_MODE=native`):
  * The duration in seconds of each audio chunk sent to the server. Defaults to `15.0`.

## Experimental Results

### `vad-stt`, `whisper-server`, and `hid-keyboard` on RPi4 with ReSpeaker 2-Mic

It seems that capturing audio (or reading WAV) and transcribing on the same RPi4 is too complicated.
The RPi4 shows significant slowness on finising the job.
Though it works, it is not practical.

### `vad-stt`, `whisper-server`, and `hid-keyboard` on RPi5 with USB sound adapter

The RPi5 shows much better performance than RPi4.
The run-time transcription speed is acceptable though it is still not real-time.

### `vad-stt` and `hid-keyboard` on RPi4, and `whisper-server` on PC

By off-loading the whisper engine to PC, we can get acceptable performance.
With my customized dietpi configuration, the link-local network is available.
We can consider contact the PC-side whisper (but the IP address may vary each time).
We can use OpenSSH to set up a remote forwarding (the RPi4 side IP is almost fixed `169.254.1.1`):

At the PC side:
```
ssh -R 8080:localhost:8080 dietpi@169.254.1.1
```

The audio is recorded at RPi4, forwarded to PC to transcribe, and back to RPi4 to inject the results
via the HID interface.

