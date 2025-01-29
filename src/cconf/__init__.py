import re

from .base import Config, config, undefined
from .ciphers import Cipher, KeyFile, Keys
from .dburl import register as register_database
from .exceptions import ConfigError, ConfigWarning, PolicyError
from .policy import UserOnly, UserOrGroup
from .sources import EnvDir, EnvFile, HostEnv, SecretsDir
from .types import (
    CacheDict,
    CommaSeparated,
    CommaSeparatedInts,
    CommaSeparatedStrings,
    DatabaseDict,
    Duration,
    Secret,
    Separated,
)

__version__ = "1.0.0"
__version_info__ = tuple(
    int(num) if num.isdigit() else str(num)
    for num in re.findall(r"([a-z]*\d+)", __version__)
)

__all__ = [
    "config",
    "register_database",
    "undefined",
    "CacheDict",
    "Cipher",
    "CommaSeparated",
    "CommaSeparatedInts",
    "CommaSeparatedStrings",
    "Config",
    "ConfigError",
    "ConfigWarning",
    "DatabaseDict",
    "Duration",
    "EnvDir",
    "EnvFile",
    "HostEnv",
    "Keys",
    "KeyFile",
    "PolicyError",
    "SecretsDir",
    "UserOnly",
    "UserOrGroup",
    "Secret",
    "Separated",
]
