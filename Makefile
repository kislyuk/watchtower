SHELL=/bin/bash

lint:
	ruff check $$(dirname */__init__.py)
	mypy --install-types --non-interactive --check-untyped-defs $$(dirname */__init__.py)

test:
	python ./test/test.py -v

init_docs:
	python -m pip install furo sphinx-copybutton
	cd docs; sphinx-quickstart

docs:
	sphinx-build docs docs/html

install:
	-rm -rf dist
	python -m pip install build
	python -m build
	python -m pip install --upgrade $$(echo dist/*.whl)[test]

.PHONY: test lint release docs

include common.mk
