# VAD STT Processor

The STT program that

1. reads input speech stream
2. creates fragments based on VAD 
3. contacts `whisper-server` to transcribe each fragments
4. sends the transcribed results to the output.

The input could be a WAV file or the microphone.
The output could be a unix socket or `stdout`.

## Build

```
sudo apt update
sudo apt install python3-dev portaudio19-dev
python -m venv .venv
.venv/bin/pip install --upgrade pip setuptools
.venv/bin/pip install -r requirements.txt
.vnev/bin/pip install -e .
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
.venv/bin/vad-stt
```

If you would like to override the input and output, use environment variables:

* `VAD_INPUT` for reading the audio data
  * `mic`: read PCM data from the microphone (the default)
  * file name: read WAV data from the file
  * `-`: read the WAV data from the stdandard input 
* `STT_OUTPUT` for writing the null-terminated strings (the format is for integrating with my [rpi-hid-keyboard](https://github.com/breeze833/rpi-hid-keyboard) project)
  * `/tmp/hid-keyboard.sock`: the default unix socket name
  * socket name: the specific unix socket name
  * `-`: dump the results to the standard output

## Experimental Results

### `vad-stt`, `whisper-server`, and `hid-keyboard` on RPi4

It seems that capturing audio (or reading WAV) and transcribing on the same RPi4 is too complicated.
The RPi4 shows significant slowness on finising the job.
Though it works, it is not practical.

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

