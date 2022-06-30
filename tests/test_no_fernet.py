import base64
import unittest

from cconf import Config, ConfigWarning, ciphers, undefined
from cconf.sources import Source


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.has_fernet = ciphers.has_fernet
        ciphers.has_fernet = False

    def tearDown(self):
        ciphers.has_fernet = self.has_fernet

    def test_no_fernet_exceptions(self):
        with self.assertRaises(RuntimeError):
            Config(Source(keys=[]))
        with self.assertRaises(RuntimeError):
            Config(Source({"KEY": "VALUE"}, keys="somefile"))("KEY", sensitive=True)

    def test_base64(self):
        config = Config({"SECRET_KEY": base64.b64encode(b"secret").decode()})
        self.assertEqual(config("SECRET_KEY", sensitive=True), "secret")

    def test_unencoded(self):
        config = Config({"SECRET_KEY": "plaintext"})
        with self.assertWarns(ConfigWarning):
            with self.assertRaises(KeyError):
                config("SECRET_KEY", sensitive=True)
        with config.debug():
            with self.assertWarns(ConfigWarning):
                value = config("SECRET_KEY", sensitive=True)
                self.assertIs(value, undefined)
