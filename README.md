# cconf

`cconf` is a library for reading configuration from various sources (such as environment
variables, environment files, and environment directories) and optionally encrypting
sensitive configurations. Sensitive configuration values are encrypted using
[Fernet](https://cryptography.io/en/latest/fernet/) tokens, which provide authenticated
crypography and the ability to specify a maximum valid lifetime (`ttl`).


## Installation

`pip install cconf`


## Usage

By default, there is a `config` singleton set up to read configuration from the process
environment variables (`os.environ`):

```python
from cconf import config

DEBUG = config("DEBUG", False, cast=bool)
```

You can add to the list of configuration sources (this will still read from `os.environ`
first):

```python
from cconf import config

config.file("/path/to/.env")
config.dir("/path/to/envdir")
```

Or you may want to set the configuration sources (and their order) manually. The
following will try `envdir` first, followed by `.env`.

```python
from cconf import config

config.setup("/path/to/envdir", "/path/to/.env")
```

You can also specify sources that have `keys`, which can be the path to a file with
`Fernet` keys, one per line, or a list of `str|bytes` keys that will be converted to
`Fernet` keys:

```python
from cconf import config, EnvDir, EnvFile, HostEnv

config.setup(
    EnvDir("/path/to/envdir", keys="/path/to/envdir.keys"),
    EnvFile("/path/to/.env", keys="/path/to/env.keys"),
    HostEnv(keys=["WQ6g4VBia1fNCuVCrsX5VvGUWYlHssUJLshONLsivhc="]),
)
```

## Encrypting Sensitive Data

Any configuration value can be marked as `sensitive`, meaning it must be encrypted (or
base64-encoded if not using `Fernet` keys) and will never be read from a plaintext
source.

```python
from cconf import config, Secret

config.file("/path/to/.env", keys="/path/to/secret.key")

# This SECRET_KEY is only valid for 24 hours.
SECRET_KEY = config("SECRET_KEY", sensitive=True, cast=Secret, ttl=86400)
```

Setting a `ttl` will ensure the encrypted value is no older than that number of seconds.
Values older than `ttl` will emit a warning and return `undefined`. You may set a
default value for a `sensitive` config value, but a warning will be emitted.

To get started, you can use the `cconf` CLI tool to generate a new `Fernet` key, then
use that key to encrypt some data:

```
% cconf genkey > secret.key
% cconf encrypt --keyfile secret.key secretdata
```

If you've already generated a key and configured the sources with that key in your
settings file, you may also pass `-c/--config` to `cconf`:

```
% cconf -c myapp.settings encrypt secretdata
```

This will encrypt the string `secretdata` using all encrypted sources in your config,
and output them along with the source they're encrypted for. You must add this data to
your configuration files manually, `cconf` makes no attempt to write to these files for
you.


## Key and File Policies

A source may specify a key file policy (`keys=cconf.KeyFile(name, policy=...)`) which
performs additional checks when opening the key file. By default `KeyFile.policy` is
set to `cconf.UserOnly`, which checks that the key file is owned by the current user,
and has no permissions granted to group or other users (i.e. `600` mode).

Similarly, `EnvFile` and `EnvDir` sources accept a `policy` argument (which defaults to
`None`) that will perform policy checks when opening the environment files. You may set
this to `cconf.UserOnly` or `cconf.UserOrGroup`, or write your own policy. A policy is
simply a function that takes a single `path` argument and raises `cconf.PolicyError` if
the file should not be opened.


## Checking Configuration

The `cconf` CLI tool includes a `check` command which will print out a list of
configuration variables it knows about, grouped by the source. For instance, running it
against the `tests.settings.prod` module of a local checkout will produce something that
looks like this:

```
% python -m cconf.cli -c tests.settings.prod check
EnvFile(/Users/dcwatson/Projects/cconf/tests/envs/prod)
    HOSTNAME
        'prodhost'
    USERNAME
        'produser'
    API_KEY
        'prodkey'
EnvDir(/Users/dcwatson/Projects/cconf/tests/envdirs/prod)
    PASSWORD
        'cc0nfRul3z!'
(Default)
    DEBUG
        'false'
```

## Warnings

`cconf` will emit warnings (specifically `ConfigWarning`, a subclass of `UserWarning`)
in certain cases:

* A config value was marked as `sensitive`, but the value extracted from the
  configuration source has either expired (if a `ttl` was specified), or is improperly
  encrypted (wrong key, plaintext, etc.)
* A config value was marked as `sensitive`, but was not found in any of the sources and
  a default value is being used.
* A config key was not found in any of the sources, and there is no default value
  specified. In this case, `undefined` is returned and a warning is emitted.

You may choose to silence these warnings, or promote them to exceptions using Python's
`warnings` module:

```python
import warnings
from cconf import ConfigWarning

# Silence all ConfigWarnings.
warnings.simplefilter("ignore", ConfigWarning)

# Raise ConfigWarnings as exceptions.
warnings.simplefilter("error", ConfigWarning)
```


## Django Integration

`cconf` includes a single management command that wraps the `cconf` CLI tool. To use it,
add `cconf` to your `INSTALLED_APPS` setting, then run `manage.py config`. Being a
management command means your settings are already imported, so you don't need to
constantly pass `-c myproject.settings` to the `cconf` CLI.
