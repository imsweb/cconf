import re
import shlex
from datetime import timedelta
from warnings import warn

from . import cacheurl, dburl


class Secret(str):
    """
    A `str` subclass whose `repr` does not show the underlying string. Useful for
    sensitive strings like passwords that you do not want to appear in tracebacks and
    such.
    """

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"{class_name}('**********')"


def CommaSeparated(python_type):
    def _parser(value):
        if isinstance(value, str):
            splitter = shlex.shlex(value, posix=True)
            splitter.whitespace = ","
            splitter.whitespace_split = True
            return [python_type(item.strip()) for item in splitter]
        else:
            return list(value)

    return _parser


CommaSeparatedStrings = CommaSeparated(str)
CommaSeparatedInts = CommaSeparated(int)


class Duration(timedelta):
    """
    A `datetime.timedelta` subclass that can be constructed with a duration string of
    the format `YyWwDdHhMmSs` where the capital letters are integers and the lowercase
    letters are duration specifiers (year/week/day/hour/minute/second). Also adds a
    `duration_string` method for converting back to this format.
    """

    SPECS = {
        "y": 31536000,
        "w": 604800,
        "d": 86400,
        "h": 3600,
        "m": 60,
        "s": 1,
    }

    SPLITTER = re.compile("([{}])".format("".join(SPECS.keys())))

    def __new__(cls, value):
        if isinstance(value, timedelta):
            return timedelta.__new__(cls, seconds=value.total_seconds())
        if value.isdigit():
            return timedelta.__new__(cls, seconds=int(value))
        parts = Duration.SPLITTER.split(value.lower().strip())
        seconds = 0
        for pair in zip(parts[::2], parts[1::2]):
            if pair:
                if pair[1] == "y":
                    warn(
                        "Using `y` as a Duration format is deprecated; use `w` or `d`.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
                seconds += int(pair[0]) * Duration.SPECS[pair[1]]
        return timedelta.__new__(cls, seconds=seconds)

    def duration_string(self):
        seconds = self.total_seconds()
        duration = []
        for fmt, sec in Duration.SPECS.items():
            if fmt == "y":
                # Years as a format specifier is on its way out.
                continue
            num = int(seconds // sec)
            if num > 0:
                duration.append("{}{}".format(num, fmt))
                seconds -= num * sec
        return "".join(duration)


def DatabaseDict(value=None, **settings):
    if settings:
        assert value is None

        def parse_wrapper(url):
            return dburl.parse(url, **settings)

        return parse_wrapper
    elif value:
        assert not settings
        return dburl.parse(value)
    else:
        raise ValueError("No database URL specified.")


def CacheDict(value=None, **settings):
    if settings:
        assert value is None

        def parse_wrapper(url):
            return cacheurl.parse(url, **settings)

        return parse_wrapper
    elif value:
        assert not settings
        return cacheurl.parse(value)
    else:
        raise ValueError("No cache URL specified.")
