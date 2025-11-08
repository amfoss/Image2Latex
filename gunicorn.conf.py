"""
Gunicorn configuration file.
This file is automatically detected by Gunicorn when you run it.
It tells Gunicorn how to spawn our AI workers and ZMQ proxy
alongside its own web workers.
"""

import os
from multiprocessing import Process
from dotenv import load_dotenv
import zmq
from worker import worker, proxy_steerer

load_dotenv()
NUM_AI_WORKERS = int(os.getenv("NUM_WORKERS", 2))
INFO = bool(os.getenv("INFO"))

worker_processes = []

def on_starting(server):
    
    if INFO:
        print(f"[INFO] Gunicorn master starting, spawning 1 ZMQ proxy and {NUM_AI_WORKERS} AI workers...")
    
    proxy_proc = Process(target=proxy_steerer, daemon=True)
    proxy_proc.start()
    worker_processes.append(proxy_proc)
    
    for _ in range(NUM_AI_WORKERS):
        p = Process(target=worker, daemon=True)
        p.start()
        worker_processes.append(p)
    
    if INFO:
        print(f"[INFO] All {NUM_AI_WORKERS + 1} background processes spawned.")
        print(f"[INFO] PIDs: {[p.pid for p in worker_processes]}")

def on_exit(server):
    
    if INFO:
        print("[INFO] Gunicorn shutting down, terminating background processes...")
    
    try:
        zmq.Context.instance().term()
        if INFO:
            print("[INFO] ZMQ Context terminated.")
    except Exception as e:
        print(f"[ERROR] Failed to terminate ZMQ context: {e}")

    for p in worker_processes:
        if p.is_alive():
            p.terminate()
            p.join(timeout=1)
    
    if INFO:
        print("[INFO] Background processes terminated.")



#gunicorn -b 0.0.0.0:8000 app:app

when_ready = on_starting
on_exit = on_exit