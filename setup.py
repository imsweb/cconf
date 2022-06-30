import os
import re

from setuptools import find_packages, setup

with open(os.path.join("cconf", "__init__.py"), "r") as src:
    version = re.match(r'.*__version__ = "(.*?)"', src.read(), re.S).group(1)

with open("README.md") as readme_md:
    readme = readme_md.read()

setup(
    name="cconf",
    version=version,
    url="https://github.com/imsweb/cconf",
    license="BSD",
    author="Dan Watson",
    author_email="watsond@imsweb.com",
    description="Multi-sourced (and optionally encrypted) configuration management.",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests", "tests.settings")),
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    extras_require={
        "fernet": ["cryptography"],
    },
    entry_points={
        "console_scripts": ["cconf=cconf.cli:main"],
    },
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)
