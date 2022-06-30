import argparse
import importlib
import json
import sys

from .ciphers import KeyFile


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
    dump = subs.add_parser("dump")
    dump.add_argument("-i", "--interactive", action="store_true")
    k8s = subs.add_parser("k8s")
    k8s.add_argument("-n", "--namespace", default=None)
    k8s.add_argument("-y", "--yaml", action="store_true")
    k8s.add_argument("name", nargs="?", default="cconf")


def check(config, **options):
    source_vars = {}
    for key in sorted(config._defined):
        configval = config._defined[key]
        source_name = "(Default)" if configval.source is None else str(configval.source)
        source_vars.setdefault(source_name, []).append((key, configval.raw))
    for source in sorted(source_vars):
        log(f"{source}")
        for key, value in source_vars[source]:
            log(f"    {key}\n        {repr(value)}")


def genkey(config, **options):
    from cryptography.fernet import Fernet

    log(Fernet.generate_key().decode())


def encrypt(config, **options):
    keyfile = options.get("keyfile")
    if keyfile:
        cipher = KeyFile(keyfile, policy=None)
        log(cipher.encrypt(options["value"][0]))
    else:
        for source in config._sources:
            log(source)
            log("    {}", source.encrypt(options["value"][0]))


def dump(config, **options):
    data = {}
    file = sys.stdout
    should_close = False
    if options["interactive"]:
        filename = input("Write to file [-]: ")
        if filename.strip() not in ("", "-"):
            file = open(filename, "w")
            should_close = True
    for key in sorted(config._defined):
        configval = config._defined[key]
        stringval = "" if configval.raw is None else str(configval.raw)
        if options["interactive"]:
            value = input(f"{key} [{stringval}]: ")
            data[key] = value.strip() or stringval
        else:
            data[key] = stringval
    for key, stringval in data.items():
        log("{}={}", key, stringval, file=file)
    if should_close:
        file.close()


def k8s(config, **options):
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
    if options["yaml"]:
        import yaml

        log(yaml.dump_all(items, sort_keys=False))
    elif len(items) == 1:
        log(json.dumps(items[0], indent=4, default=lambda obj: ""))
    else:
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
    elif action == "dump":
        dump(config, **options)
    elif action == "k8s":
        k8s(config, **options)


def main(*args):
    parser = argparse.ArgumentParser()
    setup_parser(parser)
    options = parser.parse_args(args=args or None)
    execute(**vars(options))


if __name__ == "__main__":
    main()
