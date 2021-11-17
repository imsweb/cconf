import importlib
import os
from pathlib import Path

from cconf import config

# This should not actually be used.
os.environ.setdefault("USERNAME", "root")

BASE_DIR = Path(__file__).resolve().parent.parent

# Note we're excluding environment variables as a source here.
config.setup(
    BASE_DIR / "envdirs" / "prod",
    BASE_DIR / "envs" / "prod",
    key_file=BASE_DIR / "keys" / "prod",
    key_policy=None,
)

# Normally this would just be "from .common import *" but we need to reload since
# we're importing multiple times from tests.
common = importlib.import_module("tests.settings.common")
importlib.reload(common)
