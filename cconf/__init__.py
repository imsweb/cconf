import re

from .base import Config, config, undefined
from .ciphers import Cipher, KeyFile, Keys
from .dburl import register as register_database
from .exceptions import ConfigError, ConfigWarning
from .policy import PolicyError, UserOnly, UserOrGroup
from .sources import EnvDir, EnvFile, HostEnv, SecretsDir
from .types import CacheDict, CommaSeparatedStrings, DatabaseDict, Duration, Secret

__version__ = "0.9.3"
__version_info__ = tuple(
    int(num) if num.isdigit() else num
    for num in re.findall(r"([a-z]*\d+)", __version__)
)

__all__ = [
    "config",
    "register_database",
    "undefined",
    "CacheDict",
    "Cipher",
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
]
