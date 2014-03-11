web: gunicorn app:app
worker: celery -A app:tasks worker -B