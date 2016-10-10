SHELL=/bin/bash

env: requirements.txt
	virtualenv --python=python3 env
	source env/bin/activate; pip install -r requirements.txt -r test-requirements.txt
	source env/bin/activate; pip list --outdated

lint: env
	source env/bin/activate; ./setup.py flake8

test: env lint
	source env/bin/activate; ./test/test.py -v

test3: env
	python3 ./test/test.py -v

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

.PHONY: test release docs lint

include common.mk
