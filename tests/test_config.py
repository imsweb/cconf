import os
import stat
import tempfile
import time
import unittest

from cryptography.fernet import Fernet

from cconf import (
    Config,
    ConfigWarning,
    EnvDir,
    EnvFile,
    PolicyError,
    Secret,
    UserOnly,
    undefined,
)


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

    def test_ttl(self):
        key = Fernet(Fernet.generate_key())
        past_time = int(time.time()) - 600  # 10 minutes ago
        old_value = key.encrypt_at_time(b"old-secret", past_time).decode()
        config = Config({"SECRET_KEY": old_value}, keys=[key])
        with self.assertWarns(ConfigWarning):
            value = config("SECRET_KEY", cast=Secret, sensitive=True, ttl=300)
            self.assertEqual(value, undefined)

    def test_envdir(self):
        with tempfile.TemporaryDirectory() as dirname:
            config = Config(EnvDir(dirname))
            # with self.assertRaises(KeyError):
            with self.assertWarns(ConfigWarning):
                config("SOME_KEY")
            with open(os.path.join(dirname, "SOME_KEY"), "w") as f:
                f.write("some value")
            self.assertEqual(config("SOME_KEY"), "some value")

    def test_envfile(self):
        with tempfile.TemporaryDirectory() as dirname:
            envfile = os.path.join(dirname, "env")
            config = Config(EnvFile(envfile))
            # with self.assertRaises(KeyError):
            with self.assertWarns(ConfigWarning):
                config("SOME_KEY")
            with open(envfile, "w") as f:
                f.write("# environment below\n")
                f.write("SOME_KEY=some value\n")
            self.assertEqual(config("SOME_KEY"), "some value")
            # with self.assertRaises(KeyError):
            with self.assertWarns(ConfigWarning):
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
            config = Config(
                EnvDir(dirname, key_file=key_file, key_policy=None), {"DEBUG": "true"}
            )
            self.assertTrue(config("DEBUG", cast=bool))
            self.assertEqual(
                config("DATABASE_URL", sensitive=True), "postgres://localhost"
            )

    def test_policy(self):
        key = Fernet.generate_key()
        encrypted = Fernet(key).encrypt(b"secret").decode()
        with tempfile.TemporaryDirectory() as dirname:
            key_file = os.path.join(dirname, "secret.key")
            env_file = os.path.join(dirname, "env")
            with open(key_file, "wb") as f:
                f.write(key)
            with open(env_file, "w") as f:
                f.write(f"SECRET_KEY={encrypted}")
            # Check that the default UserOnly key_policy is working.
            config = Config(EnvFile(env_file, key_file=key_file))
            with self.assertRaises(PolicyError):
                config("SECRET_KEY", sensitive=True)
            # Set the key to only readable/writable by the user and try again.
            os.chmod(key_file, stat.S_IRUSR | stat.S_IWUSR)
            self.assertEqual(config("SECRET_KEY", sensitive=True), "secret")
            # Now check the EnvFile policy.
            config = Config(EnvFile(env_file, policy=UserOnly, key_file=key_file))
            with self.assertRaises(PolicyError):
                config("SECRET_KEY", sensitive=True)
            os.chmod(env_file, stat.S_IRUSR | stat.S_IWUSR)
            self.assertEqual(config("SECRET_KEY", sensitive=True), "secret")
