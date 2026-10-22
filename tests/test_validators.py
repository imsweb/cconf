import operator
import unittest
from collections.abc import Callable
from typing import TypeVar

from cconf import Config, Matches, OneOf

T = TypeVar("T")


def MustBeTrue(value: bool):
    if value is not True:
        raise ValueError("Not true!!")


ValidEmail = Matches(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def _operator_validator(
    op: Callable[[T, T], bool],
    expr: str,
) -> Callable[[T], Callable[[T], None]]:
    def _validator(constraint: T):
        def _check(value: T):
            if not op(value, constraint):
                raise ValueError(f"{value} NOT {expr} {constraint}")

        return _check

    return _validator


LT = _operator_validator(operator.lt, "<")
GT = _operator_validator(operator.gt, ">")


class CastingTests(unittest.TestCase):
    def test_oneof(self):
        config = Config({"ENVIRONMENT": "prod"})
        key = config("ENVIRONMENT", validate=OneOf("dev", "prod"))
        self.assertEqual(key, "prod")
        with self.assertRaises(ValueError):
            config("ENVIRONMENT", validate=OneOf("dev", "test"))

    def test_custom_validate(self):
        config = Config({"DEBUG": "false"})
        with self.assertRaises(ValueError, msg="Not true!!"):
            config("DEBUG", cast=bool, validate=MustBeTrue)
        self.assertTrue(
            Config({"DEBUG": "true"})("DEBUG", cast=bool, validate=MustBeTrue)
        )

    def test_matches(self):
        with self.assertRaises(ValueError):
            Config({"EMAIL": "root@localhost"})("EMAIL", validate=ValidEmail)
        valid_email = "root@localhost.localdomain"
        email = Config({"EMAIL": valid_email})("EMAIL", validate=ValidEmail)
        self.assertEqual(email, valid_email)

    def test_multiple(self):
        config = Config({"NUM": "4"})
        num = config("NUM", cast=int, validate=[GT(0), LT(5)])
        self.assertEqual(num, 4)
        with self.assertRaises(ValueError):
            config("NUM", cast=int, validate=[GT(0), LT(4)])
        with self.assertRaises(ValueError):
            config("NUM", cast=int, validate=[GT(4), LT(10)])
