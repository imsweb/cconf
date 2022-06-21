import argparse
import importlib
import json
import sys

from cryptography.fernet import Fernet


def log(msg, *args, file=sys.stdout):
    msg = str(msg)
    if args:
        msg = msg.format(*args)
    print(msg, file=file, flush=True)


def err(msg, *args):
    log(msg, *args, file=sys.stderr)


def die(msg, *args, code=1):
    err(msg, *args)
    sys.exit(code)


def setup_parser(parser):
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument(
        "--config",
        "-c",
        default="cconf.base",
        dest="config_module",
    )
    subs = parser.add_subparsers(dest="action")
    subs.add_parser("check")
    subs.add_parser("genkey")
    encrypt = subs.add_parser("encrypt")
    encrypt.add_argument("--keyfile", default=None)
    encrypt.add_argument("value", nargs=1)
    k8s = subs.add_parser("k8s")
    k8s.add_argument("-n", "--namespace", default=None)
    k8s.add_argument("name", nargs="?", default="cconf")


def check(config, **options):
    source_vars = {}
    for key, configval in config._defined.items():
        source_name = "(Default)" if configval.source is None else str(configval.source)
        source_vars.setdefault(source_name, []).append((key, configval.raw))
    for source, items in source_vars.items():
        log(f"{source}")
        for key, value in items:
            log(f"    {key}\n        {repr(value)}")


def genkey(config, **options):
    log(Fernet.generate_key().decode())


def encrypt(config, **options):
    keyfile = options.get("keyfile")
    if keyfile:
        with open(keyfile) as f:
            key = Fernet(f.read())
            log(key.encrypt(options["value"][0].encode()).decode())
    else:
        for source in config._sources:
            if source.encrypted:
                log(source)
                log("    {}", source.encrypt(options["value"][0]))


def k8s_json(config, **options):
    data = {}
    secrets = {}
    for key in sorted(config._defined):
        configval = config._defined[key]
        stringval = "" if configval.raw is None else str(configval.raw)
        if configval.sensitive:
            secrets[key] = stringval
        else:
            data[key] = stringval
    metadata = {"name": options["name"]}
    if options["namespace"]:
        metadata["namespace"] = options["namespace"]
    items = []
    if data:
        items.append(
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": metadata,
                "data": data,
            }
        )
    if secrets:
        items.append(
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": metadata,
                "type": "Opaque",
                "stringData": secrets,
            }
        )
    objects = {
        "apiVersion": "v1",
        "kind": "List",
        "items": items,
    }
    log(json.dumps(objects, indent=4, default=lambda obj: ""))


def execute(**options):
    try:
        config_module = importlib.import_module(options["config_module"])
        config = getattr(config_module, "config")
    except ImportError:
        module_name, config_name = options["config_module"].rsplit(".", 1)
        config_module = importlib.import_module(module_name)
        config = getattr(config_module, config_name)
    action = options.get("action", "check")
    if action == "check":
        check(config, **options)
    elif action == "genkey":
        genkey(config, **options)
    elif action == "encrypt":
        encrypt(config, **options)
    elif action == "k8s":
        k8s_json(config, **options)


def main(*args):
    parser = argparse.ArgumentParser()
    setup_parser(parser)
    options = parser.parse_args(args=args or None)
    execute(**vars(options))


if __name__ == "__main__":
    main()
