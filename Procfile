web: gunicorn client.wsgi:application --bind 0.0.0.0:$PORT
# Worker will start once CELERY_BROKER_URL environment variable is configured
# worker: celery -A client worker -l info --concurrency=2