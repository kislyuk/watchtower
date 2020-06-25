SHELL=/bin/bash

test_deps:
	pip install -e .
	pip install coverage flake8 wheel pyyaml mock boto3

lint: test_deps
	./setup.py flake8

test: test_deps lint
	coverage run --source=watchtower ./test/test.py

init_docs:
	cd docs; sphinx-quickstart

docs:
	$(MAKE) -C docs html

install: clean
	python ./setup.py bdist_wheel
	pip install --upgrade dist/*.whl

clean:
	-rm -rf build dist
	-rm -rf *.egg-info

.PHONY: test release docs lint test_deps

include common.mk
