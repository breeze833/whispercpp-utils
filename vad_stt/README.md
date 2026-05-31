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
* `STT_OUTPUT` for writing the null-terminated strings
  * `/tmp/hid-keyboard.sock`: the default unix socket name
  * socket name: the specific unix socket name
  * `-`: dump the results to the standard output
