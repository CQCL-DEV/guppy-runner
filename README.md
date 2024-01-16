guppy-runner
============

## Setup

Currently this requires access to the private `guppy` repository.

If you have `poetry` and `just` installed, you can run the following to get started:

```bash
just install
just run --help
```

You must have `hugr-mlir-translate` and `hugr-mlir-opt` available in your `PATH`,
or set the following environment variables.

```bash
export HUGR_MLIR_TRANSLATE='../hugr-mlir/_b/hugr-mlir/target/x86_64-unknown-linux-gnu/debug/hugr-mlir-translate'
export HUGR_MLIR_OPT='../hugr-mlir/_b/bin/hugr-mlir-opt'
```

You also have to define the path to the compiled `qir_backend` libs from [`qir-runner`](https://github.com/qir-alliance/qir-runner).
```bash
export QIR_BACKEND_LIBS=../qir-runner/target/debug
```

Finally, you'll need `mlir-translate`, `llc`, and `clang` from the LLVM project. See [here](https://mlir.llvm.org/getting_started/) for instructions.

## Usage

Convert a `guppy` program to a `hugr` artifact:

```bash
just run test_files/even_odd.py --store-hugr hugr.json --no-run
```

This works similarly for storing the `mlir` and `llvm` artifacts:

```bash
just run test_files/even_odd.py --store-hugr hugr.msgpack --store-mlir program.mlir --store-llvm program.ll --no-run
```

The intermediary artifacts can also be used as inputs:

```bash
just run program.mlir --mlir --store-llvm program.ll --no-run
```

The input is read from stdin if no file is specified:

```bash
cat program.mlir | just run --mlir --store-llvm program.ll --no-run
```

Note that actually running the program is a work in progress.

The runner can also be used as a library,
```python
from guppy_runner import run_guppy

run_guppy("guppy.py", hugr_out="hugr.json", no_run=True)
```

## License

This project is licensed under Apache License, Version 2.0 ([LICENSE][] or http://www.apache.org/licenses/LICENSE-2.0).

  [LICENSE]: ./LICENSE
