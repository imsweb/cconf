import datetime
import os
import warnings
from typing import Any, Callable, Mapping, NamedTuple, Optional, Union

from .ciphers import DecryptError
from .exceptions import ConfigError, ConfigWarning
from .sources import BaseSource, EnvDir, EnvFile, HostEnv, Source
from .types import StrPath

BOOLEAN_STRINGS = {
    "true": True,
    "yes": True,
    "1": True,
    "false": False,
    "no": False,
    "0": False,
}


class ConfigValue(NamedTuple):
    raw: Any
    value: Any
    source: Optional[BaseSource]
    default: Any
    sensitive: bool
    ttl: Optional[int]


SourceTypes = Union[BaseSource, StrPath, Mapping[str, Any]]
CastCallable = Callable[..., Any]


class undefined:
    def __bool__(self):
        return False


class Config:
    _sources: list[BaseSource]
    _defined: dict[str, ConfigValue]

    def __init__(self, *sources: SourceTypes, **kwargs: Any):
        self._debug = False
        self._previous_debug = False
        self.setup(*sources, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *exc_details: Any):
        self._debug = self._previous_debug

    def setup(self, *sources: SourceTypes, **kwargs: Any):
        self._debug = kwargs.pop("debug", self._debug)
        self._previous_debug = self._debug
        self.reset()
        for source in sources:
            if isinstance(source, BaseSource):
                self.source(source)
            elif isinstance(source, (str, os.PathLike)):
                if not os.path.exists(source):
                    raise ConfigError(f"File or directory not found: `{source}`")
                if os.path.isdir(source):
                    self.dir(source, **kwargs)
                else:
                    self.file(source, **kwargs)
            elif isinstance(source, Mapping):  # type: ignore
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

    def debug(self, value: bool = True):
        self._previous_debug = self._debug
        self._debug = value
        return self

    def source(self, source: BaseSource):
        """
        Adds a configuration source to the list of checked sources.
        """
        self._sources.append(source)
        return self

    def file(self, path: StrPath, **kwargs: Any):
        """
        Adds an `EnvFile` source to the list of checked sources.
        """
        return self.source(EnvFile(path, **kwargs))

    def dir(self, path: StrPath, **kwargs: Any):
        """
        Adds an `EnvDir` source to the list of checked sources.
        """
        return self.source(EnvDir(path, **kwargs))

    def env(self, environ: Optional[Mapping[str, Any]] = None, **kwargs: Any):
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
        return {k: v.value for k, v in self._defined.items()}

    def __call__(
        self,
        key: str,
        default: Any = undefined,
        cast: Optional[CastCallable] = None,
        sensitive: bool = False,
        ttl: Optional[Union[int, datetime.timedelta]] = None,
    ) -> Any:
        sources_checked: list[str] = []
        key = str(key)
        if isinstance(ttl, datetime.timedelta):
            ttl = int(ttl.total_seconds())
        for source in self._sources:
            sources_checked.append(str(source))
            try:
                raw = source[key]
                if sensitive:
                    raw = source.decrypt(raw, ttl=ttl)
                value = self._perform_cast(raw, cast, key=key)
                self._defined[key] = ConfigValue(
                    raw, value, source, default, sensitive, ttl
                )
                return value
            except KeyError:
                # Config name was not found in this source, move along.
                continue
            except ConfigError as ce:
                # Config was found, but no keys were specified for a sensitive config.
                warnings.warn(str(ce), ConfigWarning, stacklevel=2)
                continue
            except DecryptError:
                # Config was found, but not (or improperly) encrypted. Move along, but
                # emit a warning.
                warnings.warn(
                    f"`{key}` found in {source} but improperly encrypted (or expired).",
                    ConfigWarning,
                    stacklevel=2,
                )
                continue
        if default is not undefined:
            value = self._perform_cast(default, cast, key=key)
            self._defined[key] = ConfigValue(
                default, value, None, default, sensitive, ttl
            )
            if sensitive and not self._debug:
                warnings.warn(
                    f"`{key}` is marked sensitive but using a default value.",
                    ConfigWarning,
                    stacklevel=2,
                )
            return value
        checked = ", ".join(sources_checked)
        if self._debug:
            warnings.warn(
                f"`{key}` has no default and was not found in any of: {checked}",
                ConfigWarning,
                stacklevel=2,
            )
        else:
            raise KeyError(f"`{key}` not found in any of: {checked}")
        return default

    def _perform_cast(self, value: Any, cast: Optional[CastCallable], key: str = ""):
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
