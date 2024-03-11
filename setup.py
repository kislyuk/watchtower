#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name="watchtower",
    version="3.1.0",
    url="https://github.com/kislyuk/watchtower",
    license="Apache Software License",
    author="Andrey Kislyuk",
    author_email="kislyuk@gmail.com",
    description="Python CloudWatch Logging",
    long_description=open("README.rst").read(),
    python_requires=">=3.8",
    install_requires=[
        "boto3 >= 1.9.253, < 2",
    ],
    extras_require={
        "tests": [
            "pyyaml",
            "ruff",
            "coverage",
            "build",
            "wheel",
            "mypy",
        ]
    },
    packages=find_packages(exclude=["test"]),
    include_package_data=True,
    package_data={
        "watchtower": ["py.typed"],
    },
    platforms=["MacOS X", "Posix"],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
