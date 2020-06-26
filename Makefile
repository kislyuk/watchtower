SHELL=/bin/bash

test_deps:
	pip install .[test]

lint: test_deps
	./setup.py flake8

test: test_deps lint
	coverage run --source=$$(python setup.py --name) -m unittest discover --start-directory test --top-level-directory . --verbose

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
