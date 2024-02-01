guppy-runner
============

## Setup
First, install [guppy](https:://github.com/CQCL/guppy).

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

Finally, you'll need `mlir-translate`, `llc`, and `clang` from the LLVM project.
See [here](https://mlir.llvm.org/getting_started/) for instructions.
Note that this should be the same version used to compile `hugr-mlir`.
You can override the default paths by setting the `MLIR_TRANSLATE`, `LLC`, and `CLANG` environment variables.

## Usage

Run your program from the command line,
```bash
just run guppy_program.py
```

Check `just run --help` for more options.

The runner can also be used as a library,
```python
from guppy_runner import run_guppy

run_guppy("guppy.py")
```

## License

This project is licensed under Apache License, Version 2.0 ([LICENSE][] or http://www.apache.org/licenses/LICENSE-2.0).

  [LICENSE]: ./LICENSE
