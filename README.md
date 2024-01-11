guppy-runner
============

## Usage

This currently requires the `guppy` repository to be cloned locally. See `pyproject.toml` for the path.

If you have `poetry` and `just` installed, you can run the following to get started:

```bash
just install
just run --help
```

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

## License

This project is licensed under Apache License, Version 2.0 ([LICENSE][] or http://www.apache.org/licenses/LICENSE-2.0).

  [LICENSE]: ./LICENSE
