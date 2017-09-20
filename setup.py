#!/usr/bin/env python

import os
from setuptools import setup, find_packages

install_requires = [line.rstrip() for line in open(os.path.join(os.path.dirname(__file__), "requirements.txt"))]
tests_require = [line.rstrip() for line in open(os.path.join(os.path.dirname(__file__), "test-requirements.txt"))]

setup(
    name="watchtower",
    version="0.4.1",
    url="https://github.com/kislyuk/watchtower",
    license="Apache Software License",
    author="Andrey Kislyuk",
    author_email="kislyuk@gmail.com",
    description="Python CloudWatch Logging",
    long_description=open("README.rst").read(),
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'test': tests_require},
    packages=find_packages(exclude=["test"]),
    platforms=["MacOS X", "Posix"],
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)
