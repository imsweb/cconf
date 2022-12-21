import os
import stat
import warnings

from .exceptions import ConfigWarning, PolicyError


def UserOnly(path):
    if os.name != "posix":
        warnings.warn(
            f"UserOnly policy for {path} is only enforced in posix environments.",
            ConfigWarning,
        )
        return
    info = os.stat(path)
    if info.st_uid != os.getuid():
        raise PolicyError(f"UID mismatch for `{path}`")
    if bool(info.st_mode & stat.S_IRWXG) or bool(info.st_mode & stat.S_IRWXO):
        raise PolicyError(f"`{path}` has `group` and/or `other` permissions.")


def UserOrGroup(path):
    if os.name != "posix":
        warnings.warn(
            f"UserOrGroup policy for {path} is only enforced in posix environments.",
            ConfigWarning,
        )
        return
    info = os.stat(path)
    if bool(info.st_mode & stat.S_IRWXO):
        raise PolicyError(f"`{path}` has `other` permissions.")


def safe_open(path, *args, **kwargs):
    policy = kwargs.pop("policy", None)
    if policy:
        policy(path)
    return open(path, *args, **kwargs)
