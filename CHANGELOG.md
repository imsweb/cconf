# 1.1.0 (TBD)

* Dropped support for Python 3.10, test on Python 3.15
* `cconf check` command outputs casted values by default now; pass `--raw` to see the raw string configs (or defaults)
* Added basic config validation (see the [README](README.md#validation) for more info)


# 1.0.0 (2025-08-21)

* Initial stable release
* Dropped Python 3.9 support
* Added type annotations throughout the code
* Cast all values to `str` by default, as all configuration sources produce strings. This means default values without an explicit cast will be cast to strings. You can pass `cast=None` to not cast the value/default (at the expense of returning an `Any`).
* Now always specify `cryptography` as a dependency (the `fernet` extra was removed)
* Boolean casts now additionally accept `t`, `y`, `f`, and `n`
* `cast`, `sensitive`, and `ttl` are now keyword-only arguments (this is technically a breaking change but all documented usage were keywords anyway)
* Added a `Recipients` cast returning `Recipient` tuples compatible with Django's `ADMINS` setting
