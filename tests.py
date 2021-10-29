import datetime
import os
import tempfile
import unittest

from cryptography.fernet import Fernet

from django_conf import (
    CommaSeparatedStrings,
    Config,
    DatabaseDict,
    Duration,
    EnvDir,
    EnvFile,
    Secret,
)


class CastingTests(unittest.TestCase):
    def test_duration(self):
        d = Duration("2w3d7h21m10s")
        self.assertIsInstance(d, Duration)
        self.assertIsInstance(d, datetime.timedelta)
        self.assertEqual(int(d.total_seconds()), 1495270)
        self.assertEqual(str(d), "17 days, 7:21:10")
        self.assertEqual(d.duration_string(), "2w3d7h21m10s")
        d = Duration("107s")
        self.assertEqual(int(d.total_seconds()), 107)
        self.assertEqual(d.duration_string(), "1m47s")
        d = datetime.date.today()
        self.assertEqual(d + Duration("2w"), d + datetime.timedelta(days=14))

    def test_dburl(self):
        config = Config({"DATABASE_URL": "postgres://user:pass@host:5555/db?timeout=0"})
        d = config("DATABASE_URL", cast=DatabaseDict)
        expected = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "db",
            "USER": "user",
            "PASSWORD": "pass",
            "HOST": "host",
            "PORT": 5555,
            "OPTIONS": {"timeout": "0"},
        }
        self.assertEqual(d, expected)
        d = config("DATABASE_URL", cast=DatabaseDict(CONN_MAX_AGE=600))
        self.assertEqual(d, {**expected, "CONN_MAX_AGE": 600})
        d = config("SQLITE_DATABASE", cast=DatabaseDict, default="sqlite:///")
        self.assertEqual(
            d,
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            },
        )

    def test_string_list(self):
        config = Config({"ALLOWED_HOSTS": "localhost, example.com"})
        hosts = config("ALLOWED_HOSTS", cast=CommaSeparatedStrings)
        self.assertEqual(hosts, ["localhost", "example.com"])


class ConfigTests(unittest.TestCase):
    def test_secret(self):
        config = Config({"SECRET_KEY": "not-very-secret"})
        key = config("SECRET_KEY", cast=Secret)
        self.assertEqual(repr(key), "Secret('**********')")
        self.assertEqual(key, "not-very-secret")

    def test_encryption(self):
        key = Fernet.generate_key()
        encrypted = Fernet(key).encrypt(b"super-secret").decode()
        config = Config({"SECRET_KEY": encrypted}, keys=[key])
        decrypted = config("SECRET_KEY", cast=Secret, sensitive=True)
        self.assertEqual(decrypted, "super-secret")

    def test_envdir(self):
        with tempfile.TemporaryDirectory() as dirname:
            config = Config(EnvDir(dirname))
            with self.assertRaises(KeyError):
                config("SOME_KEY")
            with open(os.path.join(dirname, "SOME_KEY"), "w") as f:
                f.write("some value")
            self.assertEqual(config("SOME_KEY"), "some value")

    def test_envfile(self):
        with tempfile.TemporaryDirectory() as dirname:
            envfile = os.path.join(dirname, "env")
            config = Config(EnvFile(envfile))
            with self.assertRaises(KeyError):
                config("SOME_KEY")
            with open(envfile, "w") as f:
                f.write("# environment below\n")
                f.write("SOME_KEY=some value\n")
            self.assertEqual(config("SOME_KEY"), "some value")
            with self.assertRaises(KeyError):
                config("OTHER_KEY")

    def test_multi_source(self):
        key = Fernet.generate_key()
        encrypted = Fernet(key).encrypt(b"postgres://localhost").decode()
        with tempfile.TemporaryDirectory() as dirname:
            key_file = os.path.join(dirname, "secret.key")
            with open(key_file, "wb") as f:
                f.write(key)
            with open(os.path.join(dirname, "DATABASE_URL"), "w") as f:
                f.write(encrypted)
            config = Config(EnvDir(dirname, key_file=key_file), {"DEBUG": "true"})
            self.assertTrue(config("DEBUG", cast=bool))
            self.assertEqual(
                config("DATABASE_URL", sensitive=True), "postgres://localhost"
            )
