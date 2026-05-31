import multiprocessing
from .vad_input import WavVADInput, MicVADInput
from .stt_output import StdoutOutput, SocketOutput

def run_producer_process(input_target, shared_queue, stop_event):
    """Instantiates and runs the audio producer purely inside the spawned process."""
    try:
        if input_target.lower() == "mic":
            producer_instance = MicVADInput(shared_queue)
        else:
            producer_instance = WavVADInput(input_target, shared_queue)
        
        # This will execute cleanly since webrtcvad is born here
        producer_instance.run(stop_event)
    except Exception as e:
        print(f"[Child Producer Error] Crashed during initialization: {e}", file=sys.stderr)

def run_consumer_process(output_target, shared_queue, stop_event):
    """Instantiates and runs the network consumer purely inside the spawned process."""
    try:
        if output_target == "-":
            consumer_instance = StdoutOutput(shared_queue)
        else:
            consumer_instance = SocketOutput(shared_queue, output_target)
        consumer_instance.run(stop_event)
    except Exception as e:
        print(f"[Child Consumer Error] Crashed during initialization: {e}", file=sys.stderr)

class STTDaemon:
    def __init__(self, input_target, output_target):
        self.input_target = input_target
        self.output_target = output_target
        
        # Shared IPC Queue across execution contexts
        self.shared_queue = multiprocessing.Queue()
        self.stop_event = multiprocessing.Event()
        
        self.producer_process = None
        self.consumer_process = None

    def start(self):
        # Build execution processes
        self.producer_process = multiprocessing.Process(
            target=run_producer_process,
            args=(self.input_target, self.shared_queue, self.stop_event)
        )
        self.consumer_process = multiprocessing.Process(
            target=run_consumer_process, 
            args=(self.output_target, self.shared_queue, self.stop_event)
        )

        self.producer_process.start()
        self.consumer_process.start()

    def stop(self):
        print("\n[Daemon] Signaling pipeline processes to stop...")
        self.stop_event.set()
        
        if self.producer_process:
            self.producer_process.join(timeout=5)
            if self.producer_process.is_alive():
                self.producer_process.terminate()
                
        if self.consumer_process:
            self.consumer_process.join(timeout=5)
            if self.consumer_process.is_alive():
                self.consumer_process.terminate()
        print("[Daemon] Pipeline shutdown complete.")
