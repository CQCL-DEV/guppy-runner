install:
	poetry install

tests:
	poetry run pytest

lint:
	pre-commit run --all-files

docs:
	sphinx-apidoc -f -o docs/source/ pytemplate
	sphinx-build -M html docs/source/ docs/build/

clean:
	rm -rf *.egg-info dist build docs/build

build: clean
	python -m build --sdist -n
