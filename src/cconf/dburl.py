from collections.abc import Iterable
from typing import Any, NamedTuple
from urllib.parse import parse_qs, unquote, unquote_plus, urlparse


class Engine(NamedTuple):
    backend: str
    string_ports: bool
    options: dict[str, Any]


ENGINE_SCHEMES: dict[str, Engine] = {}


def register(
    backend: str,
    schemes: Iterable[str] | None = None,
    string_ports: bool = False,
    options: dict[str, Any] | None = None,
):
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


def parse(
    url_or_config: str | dict[str, Any],
    backend: str | None = None,
    **settings: Any,
) -> dict[str, Any]:
    if isinstance(url_or_config, dict):
        return {**url_or_config, **settings}

    if url_or_config == "sqlite://:memory:":
        return {"ENGINE": ENGINE_SCHEMES["sqlite"].backend, "NAME": ":memory:"}

    url = urlparse(url_or_config)
    if url.scheme not in ENGINE_SCHEMES:
        raise ValueError(f"Unknown database scheme: {url.scheme}")
    engine = ENGINE_SCHEMES[url.scheme]
    options: dict[str, Any] = {}

    path = unquote_plus(url.path[1:].split("?")[0])
    if url.scheme == "sqlite" and path == "":
        path = ":memory:"

    port = str(url.port) if url.port and engine.string_ports else url.port

    # Pass the query string into OPTIONS.
    if url.query:
        for key, values in parse_qs(url.query).items():
            if key in engine.options:
                options.update(engine.options[key](values))
            else:
                options[key] = values[-1]

    # Allow passed OPTIONS to override query string options.
    options.update(settings.pop("OPTIONS", {}))

    # Update with environment configuration.
    config: dict[str, Any] = {"ENGINE": backend or engine.backend}
    if path:
        config["NAME"] = unquote(path)
    if url.username:
        config["USER"] = unquote(url.username)
    if url.password:
        config["PASSWORD"] = unquote(url.password)
    if url.hostname:
        config["HOST"] = url.hostname
    if port:
        config["PORT"] = port
    if options:
        config["OPTIONS"] = options

    # Update the final config with any settings passed in explicitly.
    config.update(**settings)

    return config
