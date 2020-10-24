SHELL=/bin/bash

test_deps:
	pip install coverage flake8 wheel pyyaml boto3

lint: test_deps
	./setup.py flake8

test: test_deps lint
	coverage run --source=watchtower ./test/test.py

docs:
	sphinx-build docs docs/html

install: clean
	pip install wheel
	python ./setup.py bdist_wheel
	pip install --upgrade dist/*.whl

clean:
	-rm -rf build dist
	-rm -rf *.egg-info

.PHONY: test release docs lint test_deps

include common.mk
