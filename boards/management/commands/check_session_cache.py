import uuid
from django.conf import settings
from django.core.cache import caches
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Check the configured session cache without changing user sessions"

    def handle(self, *args, **options):
        if settings.SESSION_ENGINE != "django.contrib.sessions.backends.cached_db":
            raise CommandError("Redis sessions are not enabled; set REDIS_URL first")
        cache = caches[settings.SESSION_CACHE_ALIAS]
        key = "connection-check-" + uuid.uuid4().hex
        try:
            cache.set(key, "ready", timeout=10)
            if cache.get(key) != "ready":
                raise CommandError("Session cache did not return the stored value")
            cache.delete(key)
        except (ConnectionError, TimeoutError, OSError) as error:
            raise CommandError("Session cache is unavailable") from error
        except Exception as error:
            from redis.exceptions import RedisError
            if isinstance(error, RedisError):
                raise CommandError("Session cache is unavailable") from error
            raise
        self.stdout.write("Session cache is ready")
