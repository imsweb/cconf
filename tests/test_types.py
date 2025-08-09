import datetime
import decimal
import unittest

from cconf import (
    CommaSeparated,
    CommaSeparatedInts,
    CommaSeparatedStrings,
    Config,
    DatabaseDict,
    Duration,
    Recipient,
    Recipients,
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
        self.assertEqual(Duration("2w"), Duration("1209600"))
        self.assertEqual(Duration(Duration("2w")), Duration("2w"))
        with self.assertWarns(DeprecationWarning):
            d = Duration("1y2d")
            self.assertEqual(d, Duration("367d"))
            self.assertEqual(d.duration_string(), "52w3d")

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

    def test_dburl_default(self):
        config = Config()
        expected = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
        d = config("DATABASE_URL", "sqlite:///", cast=DatabaseDict)
        self.assertEqual(d, expected)
        d = config("DATABASE_URL", expected, cast=DatabaseDict)
        self.assertEqual(d, expected)
        d = config("DATABASE_URL", expected, cast=DatabaseDict(ATOMIC_REQUESTS=True))
        self.assertEqual(d, {**expected, "ATOMIC_REQUESTS": True})

    def test_comma_separated_lists(self):
        config = Config(
            {
                "ALLOWED_HOSTS": "localhost, example.com",
                "PRIME_NUMBERS": "2 , 3 , 5 , 7 , 11",
                "DECIMALS": "3.14, 2.72",
            }
        )
        hosts = config("ALLOWED_HOSTS", cast=CommaSeparatedStrings)
        self.assertEqual(hosts, ["localhost", "example.com"])
        primes = config("PRIME_NUMBERS", cast=CommaSeparatedInts)
        self.assertEqual(primes, [2, 3, 5, 7, 11])
        decimals = config("DECIMALS", cast=CommaSeparated(decimal.Decimal))
        self.assertEqual(
            decimals,
            [
                decimal.Decimal("3.14"),
                decimal.Decimal("2.72"),
            ],
        )

    def test_recipients(self):
        config = Config(
            {"ADMINS": "Dan <d@example.com>; Alexa <a@example.com>; t@example.com"}
        )
        admins = config("ADMINS", cast=Recipients)
        self.assertEqual(
            admins,
            [
                Recipient("Dan", "d@example.com"),
                Recipient("Alexa", "a@example.com"),
                Recipient("", "t@example.com"),
            ],
        )
        admins = Config()("ADMINS", "", cast=Recipients)
        self.assertEqual(admins, [])
        config = Config({"ADMINS": "no email"})
        with self.assertRaises(ValueError):
            config("ADMINS", cast=Recipients)
