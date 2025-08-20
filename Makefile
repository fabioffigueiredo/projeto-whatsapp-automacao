run:
	python manage.py runserver

migrate:
	python manage.py makemigrations
	python manage.py migrate

superuser:
	python manage.py createsuperuser

seed:
	python manage.py seed

flushseed:
	python manage.py flushseed

reset:
	make migrate && make flushseed
