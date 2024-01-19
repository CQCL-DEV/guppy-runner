set dotenv-load
set ignore-comments

# Build the subtree projects, and install the main project dependencies.
install: _build_hugr_mlir _build_qir_runner _find_mlir_translate update
	@echo "Installation complete."

# Build the hugr-mlir compiler tools.
#
# Note that this requires building LLVM from scratch, which can take a long time.
_build_hugr_mlir:
	#!/usr/bin/env bash
	echo "Building llvm..."
	cd ext/hugr-mlir/
	nix develop --impure .# --extra-experimental-features nix-command --extra-experimental-features flakes \
		--command bash -c "cmake -B build -GNinja -DCMAKE_BUILD_TYPE=Debug && ninja -C build"

# Builds the qir-runner rust project.
_build_qir_runner:
	#!/usr/bin/env bash
	echo "Building qir-runner..."
	cd ext/qir-runner
	cargo build --release

# Finds the mlir-translate executable used by hugr-mlir, and stores it's path in `.env`
_find_mlir_translate:
	#!/usr/bin/env bash
	echo "Configuring mlir-translate..."
	cd ext/hugr-mlir
	nix develop --impure --extra-experimental-features nix-command --extra-experimental-features flakes \
		--command bash -c "nix-store -r $(which mlir-translate) | xargs -0 printf \"MLIR_TRANSLATE='%s'\n\" > ../../mlir-translate.env"
	

# Update the python dependencies.
update:
	poetry update

# Execute the guppy program runner. See `just run --help` for more information.
run *PARAMS:
	# Use the mlir-translate executable from hugr-mlir.
	set -o allexport
	source mlir-translate.env
	set +o allexport

	# Run the guppy-runner.
	poetry run guppy-runner {{PARAMS}}

# Run the code formatter and linter.
lint:
	poetry run pre-commit run --all-files

# Generate the sphinx documentation.
docs:
	sphinx-apidoc -f -o docs/source/ guppy_runner
	sphinx-build -M html docs/source/ docs/build/
