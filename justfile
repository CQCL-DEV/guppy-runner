install:
	poetry update
	poetry install

run:
	poetry run guppy-runner

lint:
	pre-commit run --all-files

docs:
	sphinx-apidoc -f -o docs/source/ pytemplate
	sphinx-build -M html docs/source/ docs/build/
