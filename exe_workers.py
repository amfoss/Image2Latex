import os
from dotenv import load_dotenv
from multiprocessing import Process

try:
    from worker import worker
except ImportError:
    print("[ERROR] Could not find 'fixed_worker.py'. Make sure the file exists.")
    exit(1)

load_dotenv()
NUM_WORKERS = int(os.getenv("NUM_WORKERS", 2)) 
INFO = bool(os.getenv("INFO"))

if __name__ == "__main__":
    print(f"[INFO] Starting {NUM_WORKERS} worker processes...")
    worker_processes = [Process(target=worker, daemon=True) for _ in range(NUM_WORKERS)]

    try:
        for p in worker_processes:
            p.start()
        
        if INFO:
            print(f"[INFO] {NUM_WORKERS} worker processes started.")
            print("[INFO] Workers are running. Press CTRL+C to stop.")
        
        for p in worker_processes:
            p.join()

    except KeyboardInterrupt:
        print("\n\nShutting Down workers from Keyboard Interrupt...")
        for p in worker_processes:
            if p.is_alive():
                p.terminate()
                p.join(timeout=1)
        print("All worker processes terminated.")
