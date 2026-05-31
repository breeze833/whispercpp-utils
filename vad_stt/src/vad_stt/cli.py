import os
import sys
import signal
import time
from .daemon import STTDaemon

def main():
    # Retrieve configurations from Environment variables with safe system defaults
    input_source = os.environ.get("VAD_INPUT", "mic")
    output_destination = os.environ.get("STT_OUTPUT", "/tmp/hid_keyboard.sock")

    print("=" * 50)
    print(" VAD-STT Pipeline Initialization")
    print(f" Source Input: {input_source}")
    print(f" Transmit Out: {output_destination}")
    print("=" * 50)

    daemon = STTDaemon(input_source, output_destination)
    daemon.start()

    # Define clean exit signal behavior
    def shutdown_handler(signum, frame):
        print(f"\n[CLI] Caught intercept signal ({signal.Signals(signum).name}).")
        pipeline.stop()
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
