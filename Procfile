release: python manage.py migrate
web: gunicorn milogistics_backend.wsgi --log-file - --bind 0.0.0.0:$PORT
