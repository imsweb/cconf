import collections
import urllib.parse as urlparse

Engine = collections.namedtuple("Engine", ["backend", "string_ports", "options"])

ENGINE_SCHEMES = {}


def register(backend, schemes=None, string_ports=False, options=None):
    if schemes is None:
        schemes = [backend.rsplit(".")[-1]]
    elif isinstance(schemes, str):
        schemes = [schemes]

    for scheme in schemes:
        # urlparse.uses_netloc.append(scheme)
        ENGINE_SCHEMES[scheme] = Engine(backend, string_ports, options or {})


# Support all the first-party Django engines out of the box.
register("django.db.backends.postgresql", ("postgres", "postgresql", "pgsql"))
register("django.contrib.gis.db.backends.postgis")
register("django.contrib.gis.db.backends.spatialite")
register("django.db.backends.mysql")
register("django.contrib.gis.db.backends.mysql", "mysqlgis")
register("django.db.backends.oracle", string_ports=True)
register("django.contrib.gis.db.backends.oracle", "oraclegis")
register("django.db.backends.sqlite3", "sqlite")


def parse(url, backend=None, **settings):
    if isinstance(url, dict):
        return {**url, **settings}

    if url == "sqlite://:memory:":
        return {"ENGINE": ENGINE_SCHEMES["sqlite"].backend, "NAME": ":memory:"}

    url = urlparse.urlparse(url)
    if url.scheme not in ENGINE_SCHEMES:
        raise ValueError(f"Unknown database scheme: {url.scheme}")
    engine = ENGINE_SCHEMES[url.scheme]
    options = {}

    path = urlparse.unquote_plus(url.path[1:].split("?")[0])
    if url.scheme == "sqlite" and path == "":
        path = ":memory:"

    port = str(url.port) if url.port and engine.string_ports else url.port

    # Pass the query string into OPTIONS.
    if url.query:
        for key, values in urlparse.parse_qs(url.query).items():
            if key in engine.options:
                options.update(engine.options[key](values))
            else:
                options[key] = values[-1]

    # Allow passed OPTIONS to override query string options.
    options.update(settings.pop("OPTIONS", {}))

    # Update with environment configuration.
    config = {"ENGINE": backend or engine.backend}
    if path:
        config["NAME"] = urlparse.unquote(path)
    if url.username:
        config["USER"] = urlparse.unquote(url.username)
    if url.password:
        config["PASSWORD"] = urlparse.unquote(url.password)
    if url.hostname:
        config["HOST"] = url.hostname
    if port:
        config["PORT"] = port
    if options:
        config["OPTIONS"] = options

    # Update the final config with any settings passed in explicitly.
    config.update(**settings)

    return config
