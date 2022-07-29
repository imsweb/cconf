import urllib.parse as urlparse

CACHE_SCHEMES = {}


class Engine:
    def __init__(self, backend, process):
        self.backend = backend
        self.process = process


def register(backend, schemes=None, process=None):
    if schemes is None:
        schemes = [backend.rsplit(".")[-1]]
    elif isinstance(schemes, str):
        schemes = [schemes]

    engine = Engine(backend, process)
    for scheme in schemes:
        CACHE_SCHEMES[scheme] = engine

    def wrapper(func):
        engine.process = func
        return func

    return wrapper


# Support all the first-party Django backends out of the box.
@register("django.core.cache.backends.locmem.LocMemCache", ("local", "locmem"))
@register("django.core.cache.backends.db.DatabaseCache", ("db", "database"))
def hostname_location(url, options):
    return url.hostname


@register("django.core.cache.backends.filebased.FileBasedCache", "file")
def path_location(url, options):
    return url.path


@register("django.core.cache.backends.memcached.PyMemcacheCache", "pymemcache")
@register("django.core.cache.backends.memcached.PyLibMCCache", "pylibmc")
def memcached_location(url, options):
    addresses = url.netloc.split(",")
    if len(addresses) == 1:
        return addresses[0]
    else:
        return addresses


@register("django.core.cache.backends.dummy.DummyCache", "dummy")
def null_location(url, options):
    return None


@register("django.core.cache.backends.redis.RedisCache", "redis")
def redis_location(url, options):
    path = url.path.lstrip("/")
    if path.isdigit() and "db" not in options:
        options["db"] = path
    return "{}://{}".format(url.scheme, url.netloc)


def parse(url, backend=None, **settings):
    if isinstance(url, dict):
        return {**url, **settings}

    url = urlparse.urlparse(url)
    if url.scheme not in CACHE_SCHEMES:
        raise ValueError(f"Unknown cache scheme: {url.scheme}")
    engine = CACHE_SCHEMES[url.scheme]
    options = {}

    # Pass the query string into OPTIONS.
    if url.query:
        for key, values in urlparse.parse_qs(url.query).items():
            if values:
                if len(values) == 1:
                    options[key] = values[0]
                else:
                    options[key] = values

    # Allow passed OPTIONS to override querystring options.
    options.update(settings.pop("OPTIONS", {}))

    # Update with environment configuration.
    config = {"BACKEND": backend or engine.backend}

    # Allow Django's cache settings to be specified as querystring options.
    for name in ("timeout", "key_prefix", "key_function", "version"):
        value = options.pop(name, None)
        if value is not None:
            if name in ("timeout", "version"):
                value = int(value)
            config[name.upper()] = value

    location = engine.process(url, options)
    if location:
        config["LOCATION"] = location
    if options:
        config["OPTIONS"] = options

    # Update the final config with any settings passed in explicitly.
    config.update(**settings)

    return config
