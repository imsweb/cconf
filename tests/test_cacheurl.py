import unittest

from cconf import CacheDict, Config


class CacheURLTests(unittest.TestCase):
    def test_default_cache(self):
        config = Config()
        expected = {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
        c = config("CACHE_URL", "dummy://", cast=CacheDict)
        self.assertEqual(c, expected)
        c = config("CACHE_URL", expected, cast=CacheDict)
        self.assertEqual(c, expected)

    def test_dummy(self):
        config = Config({"CACHE_URL": "dummy://"})
        c = config("CACHE_URL", cast=CacheDict)
        expected = {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
        self.assertEqual(c, expected)

    def test_locmem(self):
        config = Config({"CACHE_URL": "local://unique-snowflake?timeout=300&version=1"})
        c = config("CACHE_URL", cast=CacheDict)
        expected = {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
            "TIMEOUT": 300,
            "VERSION": 1,
        }
        self.assertEqual(c, expected)

    def test_redis_cache(self):
        config = Config(
            {"CACHE_URL": "redis://localhost:6379?db=1&timeout=30&version=2"}
        )
        c = config("CACHE_URL", cast=CacheDict)
        expected = {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": "redis://localhost:6379",
            "TIMEOUT": 30,
            "VERSION": 2,
            "OPTIONS": {"db": "1"},
        }
        self.assertEqual(c, expected)

    def test_redis_cache_pathdb(self):
        config = Config({"CACHE_URL": "redis://localhost:6379/5?timeout=30"})
        c = config("CACHE_URL", cast=CacheDict)
        expected = {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": "redis://localhost:6379",
            "TIMEOUT": 30,
            "OPTIONS": {"db": "5"},
        }
        self.assertEqual(c, expected)

    def test_database(self):
        config = Config({"CACHE_URL": "db://cache_table"})
        c = config("CACHE_URL", cast=CacheDict)
        expected = {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "cache_table",
        }
        self.assertEqual(c, expected)

    def test_filebased(self):
        config = Config({"CACHE_URL": "file:///path/to/cache"})
        c = config("CACHE_URL", cast=CacheDict(VERSION=1))
        expected = {
            "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
            "LOCATION": "/path/to/cache",
            "VERSION": 1,
        }
        self.assertEqual(c, expected)

    def test_pymemcache(self):
        config = Config({"CACHE_URL": "pymemcache://127.0.0.1:11211"})
        c = config("CACHE_URL", cast=CacheDict)
        expected = {
            "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
            "LOCATION": "127.0.0.1:11211",
        }
        self.assertEqual(c, expected)

    def test_pymemcache_multi(self):
        config = Config({"CACHE_URL": "pymemcache://127.0.0.1:11211,other:11234"})
        c = config("CACHE_URL", cast=CacheDict)
        expected = {
            "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
            "LOCATION": ["127.0.0.1:11211", "other:11234"],
        }
        self.assertEqual(c, expected)

    def test_pylibmc(self):
        config = Config({"CACHE_URL": "pylibmc://127.0.0.1:11211"})
        c = config("CACHE_URL", cast=CacheDict)
        expected = {
            "BACKEND": "django.core.cache.backends.memcached.PyLibMCCache",
            "LOCATION": "127.0.0.1:11211",
        }
        self.assertEqual(c, expected)

    def test_pylibmc_multi(self):
        config = Config({"CACHE_URL": "pylibmc://127.0.0.1:11211,other:11234"})
        c = config("CACHE_URL", cast=CacheDict)
        expected = {
            "BACKEND": "django.core.cache.backends.memcached.PyLibMCCache",
            "LOCATION": ["127.0.0.1:11211", "other:11234"],
        }
        self.assertEqual(c, expected)
