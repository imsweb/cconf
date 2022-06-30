import base64
import binascii
from typing import Optional, TextIO

from .exceptions import ConfigError
from .policy import UserOnly, safe_open

try:
    from cryptography.fernet import Fernet, InvalidToken, MultiFernet

    has_fernet = True
except ImportError:
    has_fernet = False


class DecryptError(Exception):
    pass


def read_keys(fileobj: TextIO):
    """
    Reads Fernet keys from a file-like object, one per line. Returns a list of Fernet
    objects.
    """
    fernets = []
    for line in fileobj.readlines():
        # TODO: skip commented out lines?
        key = line.strip()
        if key:
            fernets.append(Fernet(key))
    return MultiFernet(fernets)


class Cipher:
    secure = False

    def encrypt(self, value: str) -> str:
        raise NotImplementedError()

    def decrypt(self, value: str, ttl: Optional[int] = None) -> str:
        raise NotImplementedError()


class Keys(Cipher):
    secure = True

    def __init__(self, keyiter):
        if not has_fernet:
            raise RuntimeError("Using `Keys` requires the `cryptography` module.")
        self._keys = MultiFernet(
            [k if isinstance(k, Fernet) else Fernet(k) for k in keyiter]
        )

    def encrypt(self, value: str) -> str:
        return self._keys.encrypt(value.encode()).decode()

    def decrypt(self, value: str, ttl: Optional[int] = None) -> str:
        try:
            return self._keys.decrypt(value.encode(), ttl=ttl).decode()
        except InvalidToken:
            raise DecryptError


class KeyFile(Cipher):
    secure = True

    def __init__(self, filename: str, policy=UserOnly):
        self.filename = filename
        self.policy = policy
        self._keys = None

    def _load_keys(self):
        if not has_fernet:
            raise RuntimeError("Using `KeyFile` requires the `cryptography` module.")
        if self._keys is None:
            with safe_open(self.filename, policy=self.policy) as fileobj:
                self._keys = read_keys(fileobj)
        if not self._keys:
            raise ConfigError(f"No keys found for: {self}")

    def encrypt(self, value: str) -> str:
        self._load_keys()
        return self._keys.encrypt(value.encode()).decode()

    def decrypt(self, value: str, ttl: Optional[int] = None) -> str:
        self._load_keys()
        try:
            return self._keys.decrypt(value.encode(), ttl=ttl).decode()
        except InvalidToken:
            raise DecryptError


class Base64(Cipher):
    secure = False

    def encrypt(self, value: str) -> str:
        return base64.b64encode(value.encode()).decode()

    def decrypt(self, value: str, ttl: Optional[int] = None) -> str:
        try:
            return base64.b64decode(value.encode()).decode()
        except binascii.Error:
            raise DecryptError


class Identity:
    secure = False

    def encrypt(self, value: str) -> str:
        return value

    def decrypt(self, value: str, ttl: Optional[int] = None) -> str:
        return value
