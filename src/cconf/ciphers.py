import base64
import binascii
from collections.abc import Iterable
from typing import ClassVar, TextIO

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
    secure: ClassVar[bool]

    def encrypt(self, value: str) -> str:
        raise NotImplementedError()

    def decrypt(self, value: str, ttl: int | None = None) -> str:
        raise NotImplementedError()


class Keys(Cipher):
    secure = True

    def __init__(self, keyiter: Iterable[str | bytes | Fernet]):
        self._keys = MultiFernet(
            [k if isinstance(k, Fernet) else Fernet(k) for k in keyiter]
        )

    def encrypt(self, value: str) -> str:
        return self._keys.encrypt(value.encode()).decode()

    def decrypt(self, value: str, ttl: int | None = None) -> str:
        try:
            return self._keys.decrypt(value.encode(), ttl=ttl).decode()
        except InvalidToken:
            raise DecryptError


class KeyFile(Cipher):
    secure = True

    def __init__(self, filename: StrPath, policy: PolicyCallable | None = UserOnly):
        self._filename = filename
        self._policy = policy
        self._keys = None

    def _load_keys(self) -> MultiFernet:
        if self._keys is None:
            with safe_open(self._filename, policy=self._policy) as fileobj:
                self._keys = read_keys(fileobj)
        if not self._keys:
            raise ConfigError(f"No keys found for: {self}")
        return self._keys

    def encrypt(self, value: str) -> str:
        return self._load_keys().encrypt(value.encode()).decode()

    def decrypt(self, value: str, ttl: int | None = None) -> str:
        try:
            return self._load_keys().decrypt(value.encode(), ttl=ttl).decode()
        except InvalidToken:
            raise DecryptError


class Base64(Cipher):
    secure = False

    def encrypt(self, value: str) -> str:
        return base64.b64encode(value.encode()).decode()

    def decrypt(self, value: str, ttl: int | None = None) -> str:
        try:
            return base64.b64decode(value.encode()).decode()
        except binascii.Error:
            raise DecryptError


class Identity(Cipher):
    secure = False

    def encrypt(self, value: str) -> str:
        return value

    def decrypt(self, value: str, ttl: int | None = None) -> str:
        return value
