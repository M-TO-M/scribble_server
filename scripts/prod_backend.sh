echo
python3 manage.py makemigrations --settings=scribble.settings.base

echo
python3 manage.py migrate --settings=scribble.settings.base --fake-initial

echo
python3 manage.py collectstatic --settings=scribble.settings.base --noinput -v 3

echo
pip3 install -r /app_prod/requirements.txt

echo
gunicorn --bind 0:8000 --workers 3 --env DJANGO_SETTINGS_MODULE=scribble.settings.base scribble.wsgi:application
