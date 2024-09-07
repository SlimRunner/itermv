from setuptools import setup, find_packages

setup(
    name="itermv",
    version="0.0.1",
    packages=find_packages(exclude="test"),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "itermv = itermv.main:main",
        ]
    },
)