"""Methods for compiling HUGR-encoded guppy programs into MLIR objects."""


from enum import Enum
from pathlib import Path


class MlirMode(Enum):
    """The output format for the MLIR object."""

    BITCODE = 0
    TEXTUAL = 1


def hugr_to_mlir(hugr_msgpack: Path, mlir_out: Path | None, mode: MlirMode) -> Path:
    """Compile the input Hugr msgpack encoding a Guppy program into a LLVMIR object.

    ## Parameters
    hugr_msgpack: Path
        The path to the input Hugr msgpack file.
    mlir_out: Path | None
        The path to the output file.
    textual: bool
        Whether to produce textual LLVMIR instead of bitcode.

    ## Returns
    Returns the path to the output file.
    """
    _ = (hugr_msgpack, mlir_out, mode)
    raise NotImplementedError
