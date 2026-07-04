import os
import sys
import signal
import time
from .daemon import STTDaemon

def main():
    # Retrieve configurations from Environment variables with safe system defaults
    input_source = os.environ.get("STREAM_INPUT", os.environ.get("VAD_INPUT", "mic"))
    output_destination = os.environ.get("STREAM_OUTPUT", os.environ.get("STT_OUTPUT", "/tmp/hid_keyboard.sock"))
    stt_mode = os.environ.get("STT_MODE", os.environ.get("VAD_MODE", "webrtc")).lower()
    
    try:
        chunk_duration_s = float(os.environ.get("CHUNK_DURATION_S", "3.0"))
    except ValueError:
        chunk_duration_s = 3.0

    print("=" * 50)
    print(" Stream-STT Pipeline Initialization")
    print(f" Source Input: {input_source}")
    print(f" Transmit Out: {output_destination}")
    print(f" STT Mode:    {stt_mode}")
    if stt_mode == "native":
        print(f" Chunk Size:  {chunk_duration_s} seconds")
    print("=" * 50)

    daemon = STTDaemon(
        input_target=input_source,
        output_target=output_destination,
        stt_mode=stt_mode,
        chunk_duration_s=chunk_duration_s
    )
    daemon.start()

    # Define clean exit signal behavior
    def shutdown_handler(signum, frame):
        print(f"\n[CLI] Caught intercept signal ({signal.Signals(signum).name}).")
        daemon.stop()
        sys.exit(0)

    # Register OS Hooks
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Maintain system loop alive while processing
    while not daemon.stop_event.is_set():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            # Fallback block if signal handler doesn't catch the interrupt window
            daemon.stop()
            break

if __name__ == "__main__":
    main()
