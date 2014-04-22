# Virutelle Python-Umgebung mit django aktivieren
. ~/.virtualenvs/django-workshop/bin/activate

# Daten exportieren
python manage.py dumpdata --indent 4 questions > questions/fixtures/initial_data.json
python manage.py dumpdata --indent 4 auth.User > userauth/fixtures/initial_data.json

# SQL Queries von den Models ausführen
python manage.py syncdb

# Server starten - Seite erreichbar unter: http://127.0.0.1:8000/admin/
python manage.py runserver