import datetime
import unittest

from cconf import CommaSeparatedStrings, Config, DatabaseDict, Duration


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
        config = Config(
            {"DATABASE_URL": "postgres://user:pass%23word!@host:5555/db?timeout=0"}
        )
        d = config("DATABASE_URL", cast=DatabaseDict)
        expected = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "db",
            "USER": "user",
            "PASSWORD": "pass#word!",
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
