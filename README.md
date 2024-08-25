# boardwalk

A small shared task board built with Django and SQLite.

## Run locally

Python 3.9 or newer. SQLite is the default storage.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo --password local-demo-password
python manage.py runserver
```

Open http://127.0.0.1:8000 and sign in as `demo` with the password passed to
`seed_demo`. The command creates four example cards and is safe to repeat. It does
not reset existing account passwords. For another account use
`python manage.py createsuperuser`; there is no public registration form.

The browser can create boards and cards, move cards to the top of a column, add
comments, archive cards, and export CSV. JSON endpoints provide editing, restore,
labels, search, membership changes and work-in-progress limits. A viewer can read
and export; an editor can change cards; only the owner manages membership.

## JSON endpoints

All endpoints use the same session login as the browser. POST requests require a
CSRF cookie and matching `X-CSRFToken` header. Send `Content-Type: application/json`.

| Method | Path | Payload or query |
| --- | --- | --- |
| GET | `/api/boards/ID/cards/` | `q`, `label`, `archived=1` |
| GET | `/api/boards/ID/activity/` | Latest 100 entries |
| POST | `/api/columns/ID/cards/` | `title`, optional `description` |
| POST | `/api/cards/ID/` | `revision`, optional `title`, `description`, `archived` |
| POST | `/api/cards/ID/move/` | `revision`, `column_id`, zero-based `position` |
| POST | `/api/cards/ID/comments/` | `body` |
| POST | `/api/cards/ID/labels/` | `labels`: array of names |
| POST | `/api/columns/ID/limit/` | `limit`: integer, zero means unlimited |
| POST | `/api/boards/ID/members/` | Existing `username`, `role`: editor, viewer or remove |

Read the revision from the card list before moving or editing. A stale revision
returns 409. Moving reorders affected cards, so reload the board after a change.
Archived cards do not count toward column limits. Restore checks available room.
Unknown boards return 404; read-only writes return 403; invalid input returns 400.
Card lists return at most 200 items. CSV export includes archived cards and all
matching board rows. Formula-like cells receive a leading apostrophe.

## Docker

```sh
docker compose build
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py seed_demo --password local-demo-password
docker compose up
```

The Compose port is bound to localhost and data lives in a named volume. This uses
the Django development server. It is intended for a local demonstration, not a
public deployment. Back up the SQLite file while the app is stopped.

## Checks

```sh
pip install -r requirements-dev.txt
make test
make lint
make check
```

Tests use real Django requests and temporary database tables, including permission
boundaries, ordering, stale revisions, rollback, CSRF and CSV escaping. External
services are not needed.

## Limits

SQLite is suitable for a small personal board, not heavy concurrent writers.
Transactions keep each move together, but SQLite does not provide row-level locks;
high write contention can produce a database-locked error. Labels and membership
changes use last-write-wins semantics. There are no attachments, email invites,
due dates, realtime updates or public sharing. Search and management beyond the
basic board workflow are API-only. Activity is ordered by sequence number.

## Optional Redis sessions

Session reads can use Redis while SQLite remains the durable session store.
Board membership and card permissions are always read from the database; they are
not cached. Evicted session keys are restored from the database on the next read.
Logout removes the session from both stores.

```sh
pip install -r requirements-redis.txt
REDIS_URL=redis://127.0.0.1:6379/0 python manage.py runserver
```

Without `REDIS_URL`, the application continues to use ordinary database sessions.
With it set, Redis must be reachable. Database fallback handles cache misses, not
a Redis outage: this Django backend can fail a request if Redis cannot accept a
cache write. Connection and socket timeouts are two seconds. Do not expose the
Redis port publicly or share its database with untrusted applications.

For the optional Compose setup, use both files for each command:

```sh
docker compose -f docker-compose.yml -f docker-compose.redis.yml build
docker compose -f docker-compose.yml -f docker-compose.redis.yml run --rm web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.redis.yml up
```

The Redis service is reachable only inside the Compose network. Redis persistence
is disabled because sessions are also written to SQLite.

Integration tests require a running Redis instance and the optional dependencies:

```sh
TEST_REDIS_URL=redis://127.0.0.1:6379/1 make redis-test
```

Tests use randomly prefixed keys and remove only those keys. They verify real
cache hits without session database queries, eviction recovery, logout and board
permission revocation. They are skipped by the ordinary test run when no test
Redis URL is supplied.
