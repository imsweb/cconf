# 1.0.0

* Initial stable release
* Dropped Python 3.9 support
* Added type annotations throughout the code
* Now always specify `cryptography` as a dependency (the `fernet` extra was removed)
* Boolean casts now additionally accept `t`, `y`, `f`, and `n`
* `cast`, `sensitive`, and `ttl` are now keyword-only arguments (this is technically a breaking change but all documented usage were keywords anyway)
* Added a `Recipients` cast returning `Recipient` tuples compatible with Django's `ADMINS` setting
