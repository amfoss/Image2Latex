fuser -k 8000/tcp
fuser -k 5555/tcp
gunicorn -c gunicorn.conf.py -b 0.0.0.0:8000 app:app 
