from django.core.management.base import BaseCommand

from cconf.cli import execute, setup_parser


class Command(BaseCommand):
    def add_arguments(self, parser):
        setup_parser(parser)

    def handle(self, **options):
        if not options["action"]:
            options["action"] = "check"
        execute(**options)
