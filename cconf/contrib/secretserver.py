from cconf.sources import BaseSource


class SecretServerSource(BaseSource):
    def __init__(self, ss, prefix=None, field=None):
        self.ss = ss
        self.prefix = prefix or []
        self.field = field

    def __getitem__(self, key):
        path = "\\".join([*self.prefix, key])
        secret = self.ss.get_secret_by_path(path)
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
