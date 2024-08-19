test:
	python3 manage.py test

lint:
	python3 -m flake8 .

check:
	python3 manage.py check
	python3 manage.py makemigrations --check --dry-run
