#!/bin/sh
FILE=../estimate.db

# Virutelle Python-Umgebung mit django aktivieren
. ~/.virtualenvs/django-workshop/bin/activate

# Prüfen, ob Datenbank schon existiert
if [ -e $FILE ];
then
	echo "Export data from database: $FILE"
	# Daten exportieren
	python manage.py dumpdata --indent 4 questions > questions/fixtures/initial_data.json
	python manage.py dumpdata --indent 4 auth.User > userauth/fixtures/initial_data.json
fi

# SQL Queries von den Models ausführen
python manage.py syncdb

# Server starten - Seite erreichbar unter: http://127.0.0.1:8000/admin/
python manage.py runserver