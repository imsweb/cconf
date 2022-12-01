import warnings
from typing import Optional, Union

from delinea.secrets.server import (
    AccessTokenAuthorizer,
    DomainPasswordGrantAuthorizer,
    PasswordGrantAuthorizer,
    SecretServer,
    SecretServerError,
)

from cconf.exceptions import ConfigError
from cconf.sources import BaseSource


class SecretServerSource(BaseSource):
    def __init__(
        self,
        ss: Union[SecretServer, str],
        *,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        domain: Optional[str] = None,
        prefix: Optional[list] = None,
        field: Optional[str] = None,
    ):
        if isinstance(ss, SecretServer):
            self.ss = ss
        else:
            if token:
                if username or password or domain:
                    warnings.warn(
                        "`username`, `password`, and `domain` are not used with token "
                        "authentication.",
                        stacklevel=2,
                    )
                auth = AccessTokenAuthorizer(token)
            else:
                if not username or not password:
                    raise ValueError(
                        "Non-token authentication requires `username` and `password`."
                    )
                if domain:
                    auth = DomainPasswordGrantAuthorizer(ss, username, domain, password)
                else:
                    auth = PasswordGrantAuthorizer(ss, username, password)
            self.ss = SecretServer(ss, auth)
        self.prefix = prefix or []
        self.field = field

    def _get_secret(self, name_or_id):
        if name_or_id.isdigit():
            # Ignore the prefix if fetching a secret by ID.
            return self.ss.get_secret(name_or_id)
        else:
            # Otherwise prefix the secret name and fetch by path.
            path = "\\".join([*self.prefix, name_or_id])
            return self.ss.get_secret_by_path(path)

    def __getitem__(self, key):
        try:
            secret = self._get_secret(key)
        except SecretServerError as ex:
            raise ConfigError("{}: {}".format(key, ex.message))
        for item in secret["items"]:
            if item["isPassword"] and not self.field:
                # If field is not specified, return the first password value.
                return item["itemValue"]
            elif self.field and item["fieldName"] == self.field:
                # Otherwise return the value of the specified field.
                return item["itemValue"]
        raise KeyError(key)

    def decrypt(self, value, ttl=None):
        # Secrets come out of SS unencrypted.
        return value
