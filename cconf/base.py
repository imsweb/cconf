import datetime
import os
import stat
import warnings
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

BOOLEAN_STRINGS = {
    "true": True,
    "yes": True,
    "1": True,
    "false": False,
    "no": False,
    "0": False,
}


class undefined:
    pass


class ConfigError(Exception):
    pass


class ConfigWarning(UserWarning):
    pass


class PolicyError(Exception):
    pass


def UserOnly(path):
    info = os.stat(path)
    if os.name == "posix" and info.st_uid != os.getuid():
        raise PolicyError(f"UID mismatch for `{path}`")
    if bool(info.st_mode & stat.S_IRWXG) or bool(info.st_mode & stat.S_IRWXO):
        raise PolicyError(f"`{path}` has `group` and/or `other` permissions.")


def UserOrGroup(path):
    info = os.stat(path)
    if bool(info.st_mode & stat.S_IRWXO):
        raise PolicyError(f"`{path}` has `other` permissions.")


def safe_open(path, *args, **kwargs):
    policy = kwargs.pop("policy", None)
    if policy:
        policy(path)
    return open(path, *args, **kwargs)


def read_entries(fileobj):
    """
    Reads environment variable assignments from a file-like object. Only lines that
    contain an equal sign (=) and do not start with # (comments) are considered. Any
    leading/trailing quotes around the value portion of the assignment are stripped.
    """
    entries = {}
    for line in fileobj.readlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            entries[key.strip()] = value.strip().strip("\"'")
    return entries


def read_keys(fileobj):
    """
    Reads Fernet keys from a file-like object, one per line. Returns a list of Fernet
    objects.
    """
    fernets = []
    for line in fileobj.readlines():
        key = line.strip()
        if key:
            fernets.append(Fernet(key))
    return fernets


class BaseSource:
    """
    Minimal interface for implementing a configuration source.
    """

    # Set to True if the source is capable of encrypting/decrypting values.
    encrypted = False

    def __str__(self):
        return self.__class__.__name__

    def __getitem__(self):
        raise NotImplementedError()


class Source(BaseSource):
    def __init__(self, environ=None, key_file=None, keys=None, key_policy=UserOnly):
        assert key_file is None or keys is None, "Cannot specify `key_file` and `keys`."
        self._environ = environ or {}
        self._key_file = key_file
        self._keys = None
        if keys is not None:
            self._keys = [k if isinstance(k, Fernet) else Fernet(k) for k in keys]
        self._key_policy = key_policy
        self.encrypted = bool(self._key_file or self._keys)

    def __getitem__(self, key):
        return self._environ[key]

    def _load_keys(self):
        if self._key_file and self._keys is None:
            with safe_open(self._key_file, policy=self._key_policy) as fileobj:
                self._keys = read_keys(fileobj)
        if not self._keys:
            raise ConfigError(f"No keys found for: {self}")

    def encrypt(self, value):
        self._load_keys()
        return self._keys[0].encrypt(value.encode()).decode()

    def decrypt(self, value, ttl=None):
        self._load_keys()
        return MultiFernet(self._keys).decrypt(value.encode(), ttl=ttl).decode()


class HostEnv(Source):
    """
    A configuration source that reads from `os.environ`.
    """

    def __init__(self, **kwargs):
        super().__init__(environ=os.environ, **kwargs)


class EnvFile(Source):
    """
    A configuration source that reads from the specified file.
    """

    def __init__(self, env_file, policy=None, **kwargs):
        super().__init__(**kwargs)
        self._env_file = env_file
        self._policy = policy
        self._items = None

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self._env_file)

    def __getitem__(self, key):
        if self._items is None:
            try:
                with safe_open(self._env_file, policy=self._policy) as fileobj:
                    self._items = read_entries(fileobj)
            except OSError:
                raise KeyError(key)
        return self._items[key]


class EnvDir(Source):
    """
    A configuration source that reads from the specified directory, where each key is
    a separate file inside that directory.
    """

    def __init__(self, env_dir, policy=None, **kwargs):
        super().__init__(**kwargs)
        self._env_dir = env_dir
        self._policy = policy

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self._env_dir)

    def __getitem__(self, key):
        entry_path = os.path.join(self._env_dir, key)
        try:
            with safe_open(entry_path, policy=self._policy) as fileobj:
                return fileobj.read().strip()
        except OSError:
            raise KeyError(key)


class Config:
    def __init__(self, *sources, **kwargs):
        self.setup(*sources, **kwargs)

    def setup(self, *sources, **kwargs):
        self.reset()
        for source in sources:
            if isinstance(source, BaseSource):
                self.source(source)
            elif isinstance(source, (str, Path)):
                if not os.path.exists(source):
                    raise ConfigError(f"File or directory not found: `{source}`")
                if os.path.isdir(source):
                    self.dir(source, **kwargs)
                else:
                    self.file(source, **kwargs)
            elif hasattr(source, "__getitem__"):
                self.env(source, **kwargs)
            else:
                raise ConfigError(f"Unknown configuration source: {source}")

    def reset(self):
        """
        Resets the list of checked sources and already-defined configs.
        """
        self._sources = []
        self._defined = {}
        return self

    def source(self, source):
        """
        Adds a configuration source to the list of checked sources.
        """
        self._sources.append(source)
        return self

    def file(self, path, **kwargs):
        """
        Adds an `EnvFile` source to the list of checked sources.
        """
        return self.source(EnvFile(path, **kwargs))

    def dir(self, path, **kwargs):
        """
        Adds an `EnvDir` source to the list of checked sources.
        """
        return self.source(EnvDir(path, **kwargs))

    def env(self, environ=None, **kwargs):
        """
        Adds either a `HostEnv` source, or a generic `Source` to the list of checked
        sources, based on whether `environ` is set.
        """
        source = HostEnv(**kwargs) if environ is None else Source(environ, **kwargs)
        return self.source(source)

    @property
    def defined(self):
        """
        Returns a dictionary of all known config names mapped to their cast values.
        """
        return {k: v[1] for k, v in self._defined.items()}

    def __call__(self, key, default=undefined, cast=None, sensitive=False, ttl=None):
        checked = []
        for source in self._sources:
            if sensitive and not source.encrypted:
                # Don't check unencrypted sources for sensitive configs.
                continue
            checked.append(str(source))
            try:
                value = source[key]
                if sensitive:
                    if isinstance(ttl, datetime.timedelta):
                        ttl = int(ttl.total_seconds())
                    value = source.decrypt(value, ttl=ttl)
                python_value = self._perform_cast(key, value, cast)
                self._defined[key] = (value, python_value, source)
                return python_value
            except KeyError:
                # Config name was not found in this source, move along.
                continue
            except ConfigError as ce:
                # Config was found, but no keys were specified for a sensitive config.
                warnings.warn(str(ce), ConfigWarning, stacklevel=2)
                continue
            except InvalidToken:
                # Config was found, but not (or improperly) encrypted. Move along, but
                # emit a warning.
                warnings.warn(
                    f"`{key}` found in {source} but improperly encrypted (or expired).",
                    ConfigWarning,
                    stacklevel=2,
                )
                continue
        if default is not undefined:
            python_value = self._perform_cast(key, default, cast)
            self._defined[key] = (default, python_value, None)
            if sensitive:
                warnings.warn(
                    f"`{key}` is marked sensitive but using a default value.",
                    ConfigWarning,
                    stacklevel=2,
                )
            return python_value
        sources_checked = ", ".join(checked)
        warnings.warn(
            f"`{key}` not found in any of: {sources_checked}",
            ConfigWarning,
            stacklevel=2,
        )
        # raise KeyError(f"`{key}` not found in any of: {sources_checked}")
        return default

    def _perform_cast(self, key, value, cast=None):
        if cast is None or value is None:
            return value
        elif cast is bool and isinstance(value, str):
            try:
                return BOOLEAN_STRINGS[value.lower()]
            except KeyError:
                raise ValueError(f"Invalid boolean for `{key}`: `{value}`")
        try:
            return cast(value)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid {cast.__name__} for `{key}`: `{value}`")


# Shared singleton, configured to use environment variables by default.
config = Config(HostEnv())
