from flask import Blueprint, request, current_app, abort,jsonify
import io
from PIL import Image
from secrets import token_urlsafe
import base64
import redis.exceptions
import redis as sredis
import os
from dotenv import load_dotenv
import zmq

load_dotenv()

routes_bp = Blueprint('routes',__name__)

INFO = bool(os.getenv("INFO"))
ZMQ_WORKER_ADDRESS = os.getenv("ZMQ_WORKER_ADDRESS")
ZMQ_FRONTEND_ADDRESS = os.getenv("ZMQ_FRONTEND_ADDRESS")


context = zmq.Context.instance()
        
@routes_bp.route("/images/uploadfile/", methods=["POST"])
def upload_image():
    """
    Receives an image file from the client, stores it in zeromq push queue,
    and returns a unique ID.
    """
    
    if 'file' not in request.files:
        abort(400, description="No file part in the request.")
        
    file = request.files['file']
    
    if file.filename == '':
        abort(400, description="No selected file.")

    if not file.content_type or not file.content_type.startswith("image/"):
        abort(400, description="Invalid file type. Only image files are allowed (jpg/png).")

    try:
        image_bytes = file.read()

        try:
            Image.open(io.BytesIO(image_bytes)).verify()
        except Exception:
            abort(400, description="Invalid image data. Could not be processed.")

        img_uid = token_urlsafe(32)
        
        payload = {
            "id": img_uid,
            "data": base64.b64encode(image_bytes).decode('utf-8')
        }
        

        push_socket = None
        try:
            push_socket = context.socket(zmq.PUSH)
            push_socket.connect(ZMQ_FRONTEND_ADDRESS)
            push_socket.send_json(payload)
        except Exception as zmq_e:
            print(f"[ERROR] Failed to send to ZMQ proxy: {zmq_e}")
            abort(500, description="Failed to queue task.")
        finally:
            # Always close the short-lived socket
            if push_socket:
                push_socket.close()
        
        
        r_con:sredis.Redis = current_app.config['REDIS_CONNECTION']
        
        
        try:
            r_con.set(payload["id"], "Pending: ")
        except redis.exceptions.ConnectionError:
            print("[ERROR] Redis connection Error!")
            
        
        if INFO:
            print(f"[INFO] Posted for {img_uid}")
        
        return jsonify({
            "s": "ok",
            "id": img_uid
        })

    except Exception as e:
        print("[ERROR] processing image upload: ",e)
        abort(500, description=f"Failed to process image: {e}")

        
        
@routes_bp.route("/images/result/<string:img_uid>", methods=["GET"])
def get_result(img_uid: str):
    """
    Handle polling and getting back the processing result from Redis.
    """
    try:
        r_con :sredis.Redis= current_app.config['REDIS_CONNECTION']
        
        result = r_con.get(img_uid)
        
        if result is None:
            #here i think we can add a mechanism for stopping ddos attack!
            abort(404, description="Invalid Img_UID!")
        
        code = str(result).split(":",1)
        
        if INFO:
            print(f"[INFO] Got for {img_uid}")
            
        match code[0]:
            case "Pending":
                response = {"status":"pending"}
            case "Result":
                r_con.delete(img_uid)
                response = {"status":"done","result":code[-1]}
            case "Error":
                r_con.delete(img_uid)
                response = {"status":"error","e":code[-1]}
            case _:
                response = {"status":"unknown"}
                
        return jsonify(response)
    
    except redis.exceptions.ConnectionError as e:
        print("[ERROR] Redis connection error:", e)
        abort(500, description="Redis connection error")
    except Exception as e:
        print(f"[ERROR] Something unexpected went wrong with ID {img_uid}: {e}")
        abort(500, description="Internal Server error")
        