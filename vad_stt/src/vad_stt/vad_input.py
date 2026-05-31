import os
import sys
import time
import wave
import collections
import io
import pyaudio
import webrtcvad

class VADProcessor:
    """Base class containing shared logic for WebRTC VAD chunking."""
    def __init__(self, queue, rate=16000, frame_duration_ms=30, padding_duration_ms=400, max_speech_s=7):
        self.queue = queue
        self.rate = rate
        self.frame_duration = frame_duration_ms
        self.chunk = int(rate * frame_duration_ms / 1000)
        self.vad = webrtcvad.Vad(3) # Max aggressiveness
        
        self.num_padding_frames = int(padding_duration_ms / frame_duration_ms)
        self.ring_buffer = collections.deque(maxlen=self.num_padding_frames)
        self.triggered = False
        self.voiced_frames = []
        self.chunk_counter = 0
        os.makedirs("/tmp/whisper_chunks", exist_ok=True)

    def process_frame(self, frame, sample_width=2):
        if len(frame) != self.chunk * sample_width:
            return # Drop incomplete frames

        is_speech = self.vad.is_speech(frame, self.rate)

        if not self.triggered:
            self.ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in self.ring_buffer if speech])
            if num_voiced > 0.9 * self.ring_buffer.maxlen:
                self.triggered = True
                self.speech_start_time = time.time()
                self.voiced_frames.extend([f for f, _ in self.ring_buffer])
                self.ring_buffer.clear()
        else:
            self.voiced_frames.append(frame)
            self.ring_buffer.append((frame, is_speech))
            num_unvoiced = len([f for f, speech in self.ring_buffer if not speech])
            elapsed_time = time.time() - self.speech_start_time

            if (num_unvoiced > 0.9 * self.ring_buffer.maxlen) or (elapsed_time >= 7):
                self.triggered = False
                self.save_chunk(sample_width)
                self.voiced_frames = []
                self.ring_buffer.clear()

    def save_chunk(self, sample_width):
        self.chunk_counter += 1
        filename = f"/tmp/whisper_chunks/frag_{self.chunk_counter}_{int(time.time())}.wav"
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(sample_width)
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.voiced_frames))
        self.queue.put(filename)


class WavVADInput(VADProcessor):
    """Processes an existing WAV file or reads a streaming WAV structure from stdin."""
    def __init__(self, source_path, queue):
        super().__init__(queue)
        self.source_path = source_path

    def run(self, stop_event):
        if self.source_path == "-":
            # Wrap stdin bytes stream into file-like object
            wav_src = io.BytesIO(sys.stdin.buffer.read())
        else:
            wav_src = self.source_path

        try:
            with wave.open(wav_src, 'rb') as wf:
                if wf.getnchannels() != 1 or wf.getframerate() != self.rate:
                    print("[Input Error] WAV input must be 16000Hz and Mono.", file=sys.stderr)
                    return
                
                sample_width = wf.getsampwidth()
                while not stop_event.is_set():
                    frame = wf.readframes(self.chunk)
                    if not frame:
                        stop_event.set()
                    self.process_frame(frame, sample_width)
                    # Simulate processing pacing if running a local file rapidly
                    time.sleep(self.frame_duration / 1000.0)
        except Exception as e:
            print(f"[Input Exception] Error reading WAV source: {e}", file=sys.stderr)

class MicVADInput(VADProcessor):
    """Captures continuous audio live from the hardware microphone layer."""
    def __init__(self, queue):
        super().__init__(queue)

    def run(self, stop_event):
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=self.rate,
                            input=True, frames_per_buffer=self.chunk)
        except Exception as e:
            print(f"[Input Error] Failed to open audio device: {e}", file=sys.stderr)
            p.terminate()
            return

        while not stop_event.is_set():
            try:
                frame = stream.read(self.chunk, exception_on_overflow=False)
                self.process_frame(frame, sample_width=2)
            except Exception:
                continue

        stream.stop_stream()
        stream.close()
        p.terminate()
