import os
import sys
import time
import wave
import collections
import io
import pyaudio
import webrtcvad

class BaseChunker:
    """Base class containing shared logic for audio chunking and WAV output."""
    def __init__(self, queue, rate=16000, frame_duration_ms=30):
        self.queue = queue
        self.rate = rate
        self.frame_duration = frame_duration_ms
        self.chunk = int(rate * frame_duration_ms / 1000)
        self.chunk_counter = 0
        os.makedirs("/tmp/whisper_chunks", exist_ok=True)

    def process_frame(self, frame, sample_width=2):
        raise NotImplementedError

    def flush(self, sample_width=2):
        pass

    def save_chunk(self, frames, sample_width):
        self.chunk_counter += 1
        filename = f"/tmp/whisper_chunks/frag_{self.chunk_counter}_{int(time.time())}.wav"
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(sample_width)
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
        self.queue.put(filename)


class WebRTCVADChunker(BaseChunker):
    """Chunks audio using WebRTC Voice Activity Detection (VAD)."""
    def __init__(self, queue, rate=16000, frame_duration_ms=30, padding_duration_ms=400, max_speech_s=7):
        super().__init__(queue, rate, frame_duration_ms)
        self.vad = webrtcvad.Vad(3) # Max aggressiveness
        self.num_padding_frames = int(padding_duration_ms / frame_duration_ms)
        self.ring_buffer = collections.deque(maxlen=self.num_padding_frames)
        self.triggered = False
        self.voiced_frames = []
        self.max_speech_s = max_speech_s
        self.speech_start_time = 0

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

            if (num_unvoiced > 0.9 * self.ring_buffer.maxlen) or (elapsed_time >= self.max_speech_s):
                self.triggered = False
                self.save_chunk(self.voiced_frames, sample_width)
                self.voiced_frames = []
                self.ring_buffer.clear()

    def flush(self, sample_width=2):
        if self.voiced_frames:
            self.save_chunk(self.voiced_frames, sample_width)
            self.voiced_frames = []
            self.triggered = False
            self.ring_buffer.clear()


class FixedIntervalChunker(BaseChunker):
    """Chunks audio at fixed intervals (e.g. for Server-side Native VAD)."""
    def __init__(self, queue, rate=16000, frame_duration_ms=30, chunk_duration_s=3.0):
        super().__init__(queue, rate, frame_duration_ms)
        self.chunk_duration_s = chunk_duration_s
        self.frames_per_chunk = int(chunk_duration_s * 1000 / frame_duration_ms)
        self.frames = []

    def process_frame(self, frame, sample_width=2):
        if len(frame) != self.chunk * sample_width:
            return # Drop incomplete frames

        self.frames.append(frame)
        if len(self.frames) >= self.frames_per_chunk:
            self.save_chunk(self.frames, sample_width)
            self.frames = []

    def flush(self, sample_width=2):
        if self.frames:
            self.save_chunk(self.frames, sample_width)
            self.frames = []


class WavInput:
    """Processes an existing WAV file or reads a streaming WAV structure from stdin."""
    def __init__(self, source_path, chunker):
        self.source_path = source_path
        self.chunker = chunker

    def run(self, stop_event):
        if self.source_path == "-":
            # Wrap stdin bytes stream into file-like object
            wav_src = io.BytesIO(sys.stdin.buffer.read())
        else:
            wav_src = self.source_path

        try:
            with wave.open(wav_src, 'rb') as wf:
                if wf.getnchannels() != 1 or wf.getframerate() != self.chunker.rate:
                    print("[Input Error] WAV input must be 16000Hz and Mono.", file=sys.stderr)
                    return
                
                sample_width = wf.getsampwidth()
                while not stop_event.is_set():
                    frame = wf.readframes(self.chunker.chunk)
                    if not frame:
                        stop_event.set()
                        break
                    self.chunker.process_frame(frame, sample_width)
                    # Simulate processing pacing if running a local file rapidly
                    time.sleep(self.chunker.frame_duration / 1000.0)
                
                # Flush out any leftover audio at end-of-file
                self.chunker.flush(sample_width)
        except Exception as e:
            print(f"[Input Exception] Error reading WAV source: {e}", file=sys.stderr)


class MicInput:
    """Captures continuous audio live from the hardware microphone layer."""
    def __init__(self, chunker):
        self.chunker = chunker

    def run(self, stop_event):
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=self.chunker.rate,
                            input=True, frames_per_buffer=self.chunker.chunk)
        except Exception as e:
            print(f"[Input Error] Failed to open audio device: {e}", file=sys.stderr)
            p.terminate()
            return

        while not stop_event.is_set():
            try:
                frame = stream.read(self.chunker.chunk, exception_on_overflow=False)
                self.chunker.process_frame(frame, sample_width=2)
            except Exception:
                continue

        # Flush any remaining frames before shut down
        self.chunker.flush(sample_width=2)

        stream.stop_stream()
        stream.close()
        p.terminate()


# Backward compatibility aliases
WavVADInput = WavInput
MicVADInput = MicInput
VADProcessor = WebRTCVADChunker
