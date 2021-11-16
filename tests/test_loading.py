import importlib
import unittest

from cconf import Secret, config


class AppTest(unittest.TestCase):
    def test_dev_settings(self):
        importlib.import_module("tests.settings.dev")
        self.assertEqual(
            config.defined,
            {
                "HOSTNAME": "devhost",
                "USERNAME": "devuser",
                "PASSWORD": "cc0nfRul3z!",
                "DEBUG": True,
                "API_KEY": Secret("devkey"),
            },
        )

    def test_prod_settings(self):
        importlib.import_module("tests.settings.prod")
        self.assertEqual(
            config.defined,
            {
                "HOSTNAME": "prodhost",
                "USERNAME": "produser",
                "PASSWORD": "cc0nfRul3z!",
                "DEBUG": False,
                "API_KEY": Secret("prodkey"),
            },
        )
