import importlib
import os
from pathlib import Path

from cconf import config

# This will take precedence, since `config` has `HostEnv` as its first source.
os.environ.setdefault("USERNAME", "devuser")

BASE_DIR = Path(__file__).resolve().parent.parent

key_file = BASE_DIR / "keys" / "dev"

# These add to the default setup, which reads from the environment first.
config.dir(BASE_DIR / "envdirs" / "dev", key_file=key_file)
config.file(BASE_DIR / "envs" / "dev", key_file=key_file)

# Normally this would just be "from .common import *" but we need to reload since
# we're importing multiple times from tests.
common = importlib.import_module("tests.settings.common")
importlib.reload(common)
