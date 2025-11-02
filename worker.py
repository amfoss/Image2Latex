import os 
from dotenv import load_dotenv 
from PIL import Image
from pix2tex.cli import LatexOCR
import io 
import base64
import zmq 
import redis as sredis
import redis.exceptions
from multiprocessing import current_process
load_dotenv()


NUM_WORKERS = int(os.getenv("NUM_WORKERS"),1)#type:ignore
INFO = bool(os.getenv("INFO"))
ZMQ_WORKER_ADDRESS = "tcp://127.0.0.1:5555"

# Define two separate addresses for the proxy
ZMQ_FRONTEND_ADDRESS = "tcp://127.0.0.1:5555" # For Flask
ZMQ_BACKEND_ADDRESS = "tcp://127.0.0.1:5556"  # For Workers

def proxy_steerer():
    """
    This process acts as a simple, stable broker.
    It binds a PULL socket for the Flask app (frontend).
    It binds a PUSH socket for the workers (backend).
    It forwards all messages from frontend to backend.
    """
    context = zmq.Context()
    try:
        # Socket for Flask apps to PUSH to
        frontend = context.socket(zmq.PULL)
        frontend.bind(ZMQ_FRONTEND_ADDRESS)
        
        # Socket for Workers to PULL from
        backend = context.socket(zmq.PUSH)
        backend.bind(ZMQ_BACKEND_ADDRESS)

        if INFO:
            print(f"[INFO] ZMQ Proxy started. Frontend: {ZMQ_FRONTEND_ADDRESS}, Backend: {ZMQ_BACKEND_ADDRESS}")

        zmq.proxy(frontend, backend)

    except zmq.ContextTerminated:
        print("[INFO] ZMQ Proxy shutting down.")
    finally:
        frontend.close()#type:ignore
        backend.close()#type:ignore

def worker():
    context = zmq.Context.instance()

    socket = context.socket(zmq.PULL)
    socket.connect(ZMQ_BACKEND_ADDRESS)
    model = LatexOCR()
    
    if INFO:
        print("[INFO] Worker started!")
    try:
        redis_con = sredis.Redis(decode_responses=True)
        
        redis_con.ping()
    except redis.exceptions.ConnectionError:
        print("[ERROR] Cant Connect to Redis server!")
        return
    
    try:
        while True:
            try:
                
                task :dict = socket.recv_json()#type:ignore
                img_uid = task["id"]
                if INFO:
                    print(f"[INFO]{current_process().pid} Client Image {img_uid} procesing!")
                    
                img_b64_string = task["data"]
                try:
                    img_bytes = base64.b64decode(img_b64_string)
                    img_stream = io.BytesIO(img_bytes)
                    img = Image.open(img_stream)
                    result = model(img)
                    img_stream.close()
                    
                    redis_con.set(img_uid,f"Result:{str(result)}")
                    if INFO:
                        print(f"[INFO] Client Image {img_uid} procesing finished!: {result}")
                except Exception as ex:
                    redis_con.set(img_uid,f"Error:{ex}")
                
            except zmq.ZMQError as e:
                print("[ERROR] Worker: ZMQ Error",e)
                break         
            except Exception as e:
                print("[ERROR] Unexpected Error while processing image: ",e)
    except Exception as e:
        print("[ERROR] Unexpected Error from worker: ",e)
    finally:    
        socket.close()
        context.term()
        redis_con.close()
        print("[INFO] Worker shutting down.")
  