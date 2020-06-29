#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="watchtower",
    version="0.8.0",
    url="https://github.com/kislyuk/watchtower",
    license="Apache Software License",
    author="Andrey Kislyuk",
    author_email="kislyuk@gmail.com",
    description="Python CloudWatch Logging",
    long_description=open("README.rst").read(),
    install_requires=[
        "boto3 >= 1.9.253, < 2",
    ],
    tests_require=[
        "pyyaml >= 5.3.1, < 6",
        "flake8 >= 3.7.9, < 4"
    ],
    packages=find_packages(exclude=["test"]),
    platforms=["MacOS X", "Posix"],
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)
