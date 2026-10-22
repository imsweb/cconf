from argparse import Namespace

from django.core.management.base import BaseCommand

from cconf.cli import execute, setup_parser


class Command(BaseCommand):
    def add_arguments(self, parser):
        setup_parser(parser)

    def handle(self, **options):
        if not options["action"]:
            options["action"] = "check"
        if "raw" not in options:
            options["raw"] = False
        execute(Namespace(**options))
