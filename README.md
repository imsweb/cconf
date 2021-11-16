# cconf

cconf is a library for reading configuration from various sources (such as environment
variables, environment files, and environment directories) and optionally encrypting
sensitive configurations.


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

You can also specify sources that have either a `key_file` (a file with `Fernet` keys,
one per line), or `keys` (a list of `Fernet` keys or strings/bytes that will be
converted to `Fernet` keys):

```python
from cconf import config, EnvDir, EnvFile, HostEnv

config.setup(
    EnvDir("/path/to/envdir", key_file="/path/to/envdir.keys"),
    EnvFile("/path/to/.env", key_file="/path/to/env.keys"),
    HostEnv(keys=["WQ6g4VBia1fNCuVCrsX5VvGUWYlHssUJLshONLsivhc="]),
)
```

## Encrypting Sensitive Data

Any configuration value can be marked as `sensitive`, meaning it will only be read from
sources that have encryption keys, and will always be decrypted using those keys (so no
plaintext values allowed).

```python
from cconf import config, Secret
config.file("/path/to/.env", key_file="/path/to/secret.key")
SECRET_KEY = config("SECRET_KEY", sensitive=True, cast=Secret)
```

You may set a default value for a `sensitive` config value, but a warning will be
emitted.

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

## Django Integration

`cconf` includes a single management command that wraps the `cconf` CLI tool. To use it,
add `cconf` to your `INSTALLED_APPS` setting, then run `manage.py config`. Being a
management command means your settings are already imported, so you don't need to
constantly pass `-c myproject.settings` to the `cconf` CLI.
