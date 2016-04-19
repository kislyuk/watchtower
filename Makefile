SHELL=/bin/bash

env: requirements.txt
	virtualenv --python=python3 env
	source env/bin/activate; pip install --requirement=requirements.txt
	source env/bin/activate; pip list --outdated

lint:
	./setup.py flake8

test: env lint
	source env/bin/activate; ./test/test.py -v

test3: env
	python3 ./test/test.py -v

release: docs
	python setup.py sdist bdist_wheel upload -s -i D2069255

init_docs:
	cd docs; sphinx-quickstart

docs:
	$(MAKE) -C docs html

install:
	./setup.py install

.PHONY: test release docs lint
