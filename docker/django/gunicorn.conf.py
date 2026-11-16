# Gunicorn settings
# The number of workers comes from WEB_CONCURRENCY (read by Gunicorn itself)

bind = "0.0.0.0:8000"

# Load the application before forking the workers (like uwsgi)
preload_app = True

# Restart a worker stuck on a request for more than 30 s (like uwsgi harakiri)
timeout = 30

# Recycle the workers to avoid consequences of a memory leak (the jitter avoids restarting them all at once)
max_requests = 5000
max_requests_jitter = 500

# Pod's root filesystem is read-only: the worker heartbeat files are in a tmpfs
worker_tmp_dir = "/dev/shm"
