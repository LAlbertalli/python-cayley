#!/usr/bin/python
#

#Setup Package

from setuptools import setup, find_packages

setup(
    name = "cayley",
    version = "0.0.1",
    packages = find_packages(exclude=["tests"]),
    install_requires = ["requests >= 2.3.0","six >= 1.4"]
)