import os
import tempfile
import unittest

from cryptography.fernet import Fernet

from cconf import Config, EnvDir, EnvFile, Secret


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
            # with self.assertRaises(KeyError):
            with self.assertWarns(UserWarning):
                config("SOME_KEY")
            with open(os.path.join(dirname, "SOME_KEY"), "w") as f:
                f.write("some value")
            self.assertEqual(config("SOME_KEY"), "some value")

    def test_envfile(self):
        with tempfile.TemporaryDirectory() as dirname:
            envfile = os.path.join(dirname, "env")
            config = Config(EnvFile(envfile))
            # with self.assertRaises(KeyError):
            with self.assertWarns(UserWarning):
                config("SOME_KEY")
            with open(envfile, "w") as f:
                f.write("# environment below\n")
                f.write("SOME_KEY=some value\n")
            self.assertEqual(config("SOME_KEY"), "some value")
            # with self.assertRaises(KeyError):
            with self.assertWarns(UserWarning):
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
