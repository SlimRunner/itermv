import os
from setuptools import setup, find_packages

version = {}
with open(os.path.join(os.path.dirname(__file__), "itermv/version.py")) as f:
    exec(f.read(), version)

setup(
    name="itermv",
    version=version["__version__"],
    packages=find_packages(exclude="test"),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "itermv = itermv.main:main",
        ]
    },
)
