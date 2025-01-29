import base64
import binascii
from typing import Iterable, Optional, TextIO, Union

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from .exceptions import ConfigError
from .policy import PolicyCallable, UserOnly, safe_open
from .types import StrPath


class DecryptError(Exception):
    pass


def read_keys(fileobj: TextIO) -> MultiFernet:
    """
    Reads Fernet keys from a file-like object, one per line. Returns a list of Fernet
    objects.
    """
    fernets: list[Fernet] = []
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

    def __init__(self, keyiter: Iterable[Union[str, bytes, Fernet]]):
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
    _keys: Optional[MultiFernet] = None

    def __init__(self, filename: StrPath, policy: Optional[PolicyCallable] = UserOnly):
        self.filename = filename
        self.policy = policy

    def _load_keys(self):
        if self._keys is None:
            with safe_open(self.filename, policy=self.policy) as fileobj:
                self._keys = read_keys(fileobj)
        if not self._keys:
            raise ConfigError(f"No keys found for: {self}")
        return self._keys

    def encrypt(self, value: str) -> str:
        return self._load_keys().encrypt(value.encode()).decode()

    def decrypt(self, value: str, ttl: Optional[int] = None) -> str:
        try:
            return self._load_keys().decrypt(value.encode(), ttl=ttl).decode()
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
