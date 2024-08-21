import os
import unittest
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.cached_db import SessionStore
from django.contrib.sessions.models import Session
from django.core.cache import caches
from django.test import TestCase, override_settings
from .models import Membership
from .services import create_board


@unittest.skipUnless(os.environ.get("TEST_REDIS_URL"), "Set TEST_REDIS_URL for Redis integration")
class RedisSessionTests(TestCase):
    def setUp(self):
        import redis
        self.prefix = "boardwalk-test-" + uuid.uuid4().hex
        self.redis = redis.Redis.from_url(os.environ["TEST_REDIS_URL"])
        self.redis.ping()
        self.config = override_settings(
            SESSION_ENGINE="django.contrib.sessions.backends.cached_db",
            SESSION_CACHE_ALIAS="sessions",
            CACHES={
                "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
                "sessions": {
                    "BACKEND": "django.core.cache.backends.redis.RedisCache",
                    "LOCATION": os.environ["TEST_REDIS_URL"],
                    "KEY_PREFIX": self.prefix,
                    "OPTIONS": {"socket_connect_timeout": 2, "socket_timeout": 2},
                },
            })
        self.config.enable()
        self.addCleanup(self.config.disable)
        self.addCleanup(self.clean_cache)

    def clean_cache(self):
        for key in self.redis.scan_iter(match=self.prefix + ":*"):
            self.redis.delete(key)
        self.redis.close()

    def test_cache_hit_avoids_session_query(self):
        session = SessionStore()
        session["message"] = "stored in both backends"
        session.save()
        self.assertTrue(Session.objects.filter(session_key=session.session_key).exists())
        with self.assertNumQueries(0):
            loaded = SessionStore(session.session_key)
            self.assertEqual(loaded["message"], "stored in both backends")

    def test_cache_eviction_falls_back_to_database(self):
        session = SessionStore()
        session["message"] = "durable"
        session.save()
        cache = caches[settings.SESSION_CACHE_ALIAS]
        cache.delete(session.cache_key)
        with self.assertNumQueries(1):
            self.assertEqual(SessionStore(session.session_key)["message"], "durable")
        self.assertEqual(cache.get(session.cache_key)["message"], "durable")

    def test_logout_removes_database_and_cached_session(self):
        user = get_user_model().objects.create_user("reader")
        self.client.force_login(user)
        key = self.client.session.session_key
        store = SessionStore(key)
        self.assertIsNotNone(caches["sessions"].get(store.cache_key))
        self.client.post("/accounts/logout/")
        self.assertFalse(Session.objects.filter(session_key=key).exists())
        self.assertIsNone(caches["sessions"].get(store.cache_key))

    def test_cached_login_does_not_cache_board_permissions(self):
        users = get_user_model().objects
        owner = users.create_user("owner")
        reader = users.create_user("reader")
        board = create_board(owner, "Private")
        membership = Membership.objects.create(board=board, user=reader, role="viewer")
        self.client.force_login(reader)
        url = "/boards/%s/" % board.id
        self.assertEqual(self.client.get(url).status_code, 200)
        membership.delete()
        self.assertEqual(self.client.get(url).status_code, 404)
