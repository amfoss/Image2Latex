import redis as sredis 
import redis.exceptions 
from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from RequestsHandle import routes_bp

load_dotenv()

INFO = bool(os.getenv("INFO"))
NUM_WORKERS = int(os.getenv("NUM_WORKERS", 1)) 

print("Flask application starting up...")

try:

    redis_con = sredis.Redis(decode_responses=True)
    redis_con.ping()
    if INFO:
        print("[INFO] Connected to Redis at localhost:6379")
        
except redis.exceptions.ConnectionError:
    print("[ERROR] Cannot connect to Redis server at localhost:6379!")
    exit(1)

app = Flask(__name__)


app.config['REDIS_CONNECTION'] = redis_con
app.config['INFO'] = INFO

####################### CORS CONFIG
origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "null",
    "http://127.0.0.1:5000",
    "http://172.24.160.1:5000",
    "http://172.24.160.1:5500",
    "http://localhost:8000"
]
CORS(app, resources={r"/*": {"origins": origins}}, supports_credentials=True)


app.register_blueprint(routes_bp, prefix="/images")

@app.route("/")
def root():
    """
    Root Endpoint
    """
    if app.config['INFO']:
        print("[INFO] root initiated!")
    return jsonify({
        "message": "Image2Latex server is running. POST images to /images/uploadfile/"
    })
    