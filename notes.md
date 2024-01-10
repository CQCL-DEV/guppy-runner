Full pipeline:

# Guppy -> Hugr

- Import .py, call `compile()` on `main: GuppyModule` an serialize into a hugr.

# Hugr -> MLIR

- `hugr-mlir-translate --hugr-rmp-to-mlir hugr.msgpack > t.mlir`

Similarly, `--hugr-json-to-mlir`.

There's also the inverse options `--mlir-to-hugr-rmp` and `--mlir-to-hugr-json`.

# MLIR -> LLVM

- `hugr-mlir-opt t.mlir --lower-hugr`

To just show the mlir:

- `hugr-mlir-opt t.mlir`


# LLVM -> Executable
