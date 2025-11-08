# am-Latex

This is **high performance, scalable backend API system** to convert image to latex code.
This is built using modern Python stack (Flask,ZeroMQ, Redis). 

(Note: This software is tightly developed for Linux Systems 
(Backend needs a *linux* distro that's all!))
(Also: I have no idea this is will work!! not battle testes *yet*)(now it is partially tested!)
## How this works?

This isn't just a simple API; it's a full-on multiprocess worker system. When you're dealing with a "slow" task like running an OCR model, you can't just make the user wait for 5 seconds. The browser will time out, and it's a bad experience.
You can change the host and ports , even on different machines , flask and zeromq can handle those tasks at ease.

***Here's the data flow:*** 
#### ***For client part you can refer index.html file in clientcode folder or the tester.py . We need json parsing for flask***

1.**Submit (POST)**: A client sends an image to the POST /images/uploadfile/ endpoint.

2.**API (Flask)**: The API server doesn't do the work. It validates the image, generates a unique img_uid, and immediately pushes the job (the image and its ID) into a ZeroMQ message queue.

3.**Instant Response**: The server instantly replies to the client with {"id": "img_uid"}. The client now has a "ticket" for their job.

4.**Workers (multiprocessing)**: In the background, a pool of worker processes is constantly listening to the ZMQ queue. One of them (the next one available) grabs the job.These workers are the real ones who run the **OCRmodel**. 

5.**Processing**: The worker loads the LatexOCR model, processes the image, and gets the result.

6.**Store Result (Redis)**: The worker then writes the result (or any error) to a Redis database using the img_uid as the key.

7.**Polling (GET)**: Meanwhile, the client (who got the img_uid) starts asking the GET /images/result/{img_uid} endpoint, "Is it done yet?".

8.**Final Response**: The API server checks Redis.

9.**If the key says "Pending"**: It replies {"status": "pending"}.

10.**If the key says "Result:..."**: It replies {"status": "done", "result": "..."}, deletes the key, and the job is finished!

## Setup & Running
-> Python 3.12+
-> Running Redis server (on default port)
-> Python uv 

### Installation
1. Clone the repo:
`git clone [https://github.com/Nova-Stark/am-latex.git](https://github.com/Nova-Stark/am-latex.git)`
`cd am-latex`

2. Install Packages using uv 
`uv venv`
`uv init`
`uv add "flask" "flask-cors" "pix2tex[api]" python-dotenv pyzmq "redis[hiredis]" uvicorn`

3. You can edit number of workers in .env file
`NUM_WORKERS=2`
(Adjust NUM_WORKERS based on your machine's CPU cores and available RAM.)

4. Running the Application:
Make sure your Redis server is running. Then, start the main server:

Inside virtual environment 
run `python main.py`
For Production use :
`./start` after giving required permissions


This single command starts:

->The Flask web server on http://127.0.0.1:8000
->The ZMQ PUSH socket
->The pool of NUM_WORKERS child processes


## API Docu

1. Submit Image

Submits a new image for LaTeX conversion.
Endpoint: POST `/images/uploadfile/`
Body: multipart/form-data
Parameter: file (Your image file, e.g., .png, .jpg)

Success Response (Status 200)
The server accepted your job and gives you a "ticket" (the ID).

```json
{
  "s": "ok",
  "id": "2P_1l-u81...kH-S7iT5w"
}
```

Error Response (Status 400)
You sent a file that wasn't a valid image.

```json
{
  "detail": "Invalid file type. Only image files are allowed. Use jpg/png."
}

```

2. Get Result

Poll this endpoint to check the status and get the result.
Endpoint: GET /images/result/{img_uid}
URL Parameter: img_uid (The id you got from the POST request)

Pending Response
The job is still in the queue or being processed. Keep polling every few seconds.

```json
{
  "status": "pending"
}
```

Done Response
The job is complete! The result is in the result field.

```json
{
  "status": "done",
  "result": "\\frac{1}{2\\pi} \\int_{0}^{2\\pi} e^{i\\omega t} d\\omega"
}
```
Error Response
The worker tried to process the image but failed (e.g., the image was corrupt or the model couldn't find an equation).

```json
{
  "status": "error",
  "e": "Specific error message from the model"
}
```

Invalid ID Response (Status 404)
The img_uid doesn't exist (or the job has already been retrieved and deleted).
```json
{
  "detail": "Invalid Img_UID!"
}
```

## ADD-ONS perferred
->better autoscalable loadbalancer
->ratelimiter
->ddos preventer

## ABout Client
Clients can be off any language!. even it can be browser extension or website no probs!!!

# Thank YOU for reading this much .. 
# The truth is i have no idea whether it will run or not .. please contribute!!!