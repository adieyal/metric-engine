.PHONY: install test cov lint build docs clean

install:
	pip install -e .[test,docs]

test:
	pytest

cov:
	pytest --cov=metricengine --cov-report=term-missing:skip-covered --cov-report=xml

lint:
	ruff check .

docs:
	cd docs && python -m sphinx -b html . _build/html

build:
	python -m build

clean:
	rm -rf build dist *.egg-info .pytest_cache .coverage htmlcov docs/_build
