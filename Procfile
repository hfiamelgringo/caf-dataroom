web: python manage.py migrate && python manage.py load_content && python manage.py collectstatic --noinput && gunicorn caf_project.wsgi --bind 0.0.0.0:$PORT
