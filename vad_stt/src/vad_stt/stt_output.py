import os
import sys
import time
import socket
import requests

class STTOutputProcessor:
    def __init__(self, queue, whisper_url="http://127.0.0.1:8080/inference"):
        self.queue = queue
        self.whisper_url = whisper_url

    def emit_text(self, text):
        pass

    def run(self, stop_event):
        while not stop_event.is_set() or not self.queue.empty():
            try:
                # Use a timeout so loop can periodically evaluate the stop_event
                wav_filename = self.queue.get(timeout=0.5)
            except Exception:
                continue

            if not os.path.exists(wav_filename):
                continue

            try:
                with open(wav_filename, 'rb') as f:
                    files = {'file': (os.path.basename(wav_filename), f, 'audio/wav')}
                    response = requests.post(self.whisper_url, files=files, timeout=10)
                
                if response.status_code == 200:
                    transcript = response.json().get("text", "").strip()
                    if transcript:
                        self.emit_text(transcript)
            except Exception as e:
                print(f"\n[Output Error] Whisper communication exception: {e}", file=sys.stderr)
            finally:
                try:
                    os.remove(wav_filename)
                except OSError:
                    pass
            
class StdoutOutput(STTOutputProcessor):
    def __init__(self, queue, whisper_url="http://127.0.0.1:8080/inference"):
        super().__init__(queue, whisper_url)
        self.queue = queue
        
    def emit_text(self, text):
        sys.stdout.write(f"{text}\0")
        sys.stdout.flush()


class SocketOutput(STTOutputProcessor):
    def __init__(self, queue, socket_path, whisper_url="http://127.0.0.1:8080/inference"):
        super().__init__(queue, whisper_url)
        self.queue = queue
        self.socket_path = socket_path
        self.sock = None
           
    def emit_text(self, text):
        try:
            payload = f"{text}\0"
            self.sock.sendall(payload.encode('utf-8'))
        except Exception as e:
            print(f"\n[Output Error] Direct socket write failed: {e}", file=sys.stderr)
    
    def run(self, stop_event):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as self.sock:
            try:
                self.sock.connect(self.socket_path)
                super().run(stop_event)
            except Exception as e:
                print(f"[Output Warning] Can't connect to UDS socket: {e}", file=sys.stderr)
            finally:
                if self.sock:
                    self.sock.close()

