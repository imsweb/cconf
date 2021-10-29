import os

from cryptography.fernet import Fernet, MultiFernet

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


def read_entries(fileobj):
    entries = {}
    for line in fileobj.readlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            entries[key.strip()] = value.strip().strip("\"'")
    return entries


def read_keys(fileobj):
    fernets = []
    for line in fileobj.readlines():
        key = line.strip()
        if key:
            fernets.append(Fernet(key))
    return fernets


class Source:
    def __init__(self, environ=None, key_file=None, keys=None):
        assert key_file is None or keys is None, "Cannot specify `key_file` and `keys`."
        self._environ = environ or {}
        self._key_file = key_file
        self._keys = None
        if keys is not None:
            self._keys = [Fernet(k) for k in keys]

    def __repr__(self):
        return self.__class__.__name__

    def __getitem__(self, key):
        return self._environ[key]

    def decrypt(self, value):
        if self._key_file and self._keys is None:
            with open(self._key_file) as fileobj:
                self._keys = read_keys(fileobj)
        if not self._keys:
            raise ConfigError(f"No decryption keys found for {repr(self)}")
        return MultiFernet(self._keys).decrypt(value.encode()).decode()


class HostEnv(Source):
    def __init__(self):
        super().__init__(environ=os.environ)


class EnvFile(Source):
    def __init__(self, env_file, **kwargs):
        super().__init__(**kwargs)
        self._env_file = env_file
        self._items = None

    def __getitem__(self, key):
        if self._items is None:
            try:
                with open(self._env_file) as fileobj:
                    self._items = read_entries(fileobj)
            except OSError:
                raise KeyError(key)
        return self._items[key]


class EnvDir(Source):
    def __init__(self, env_dir, **kwargs):
        super().__init__(**kwargs)
        self._env_dir = env_dir

    def __getitem__(self, key):
        entry_path = os.path.join(self._env_dir, key)
        try:
            with open(entry_path) as fileobj:
                return fileobj.read()
        except OSError:
            raise KeyError(key)


class Config:
    def __init__(self, *sources, **kwargs):
        self._sources = []
        for source in sources:
            if isinstance(source, Source):
                self._sources.append(source)
            elif hasattr(source, "__getitem__"):
                self._sources.append(Source(environ=source, **kwargs))
            else:
                raise ConfigError(f"Unknown configuration source: {source}")

    def __call__(self, key, default=undefined, cast=None, sensitive=False):
        checked = []
        for source in self._sources:
            checked.append(repr(source))
            try:
                value = source[key]
                if sensitive:
                    value = source.decrypt(value)
                return self._perform_cast(key, value, cast)
            except KeyError:
                continue
        if default is not undefined:
            return self._perform_cast(key, default, cast)
        sources_checked = ", ".join(checked)
        raise KeyError(f"`{key}` not found in any of: {sources_checked}")

    def _perform_cast(self, key, value, cast=None):
        if cast is None or value is None:
            return value
        elif cast is bool and isinstance(value, str):
            try:
                return BOOLEAN_STRINGS[value.lower()]
            except KeyError:
                raise ValueError(f"Invalid boolean for {key}: `{value}`")
        try:
            return cast(value)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid {cast.__name__} for {key}: `{value}`")
