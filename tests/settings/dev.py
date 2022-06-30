import importlib
import os
from pathlib import Path

from cconf import KeyFile, config

# This will take precedence, since `config` has `HostEnv` as its first source.
os.environ.setdefault("USERNAME", "devuser")

BASE_DIR = Path(__file__).resolve().parent.parent

# Set the policy to None, since git won't keep file permissions.
key_file = KeyFile(BASE_DIR / "keys" / "dev", policy=None)

# These add to the default setup, which reads from the environment first.
config.dir(BASE_DIR / "envdirs" / "dev", keys=key_file)
config.file(BASE_DIR / "envs" / "dev", keys=key_file)

# Normally this would just be "from .common import *" but we need to reload since
# we're importing multiple times from tests.
common = importlib.import_module("tests.settings.common")
importlib.reload(common)
