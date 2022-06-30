import os
import stat


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
