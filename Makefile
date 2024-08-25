test:
	python3 manage.py test

lint:
	python3 -m flake8 .

check:
	python3 manage.py check
	python3 manage.py makemigrations --check --dry-run

redis-test:
	test -n "$(TEST_REDIS_URL)"
	python3 manage.py test boards.test_sessions
