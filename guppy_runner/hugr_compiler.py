"""Methods for compiling HUGR-encoded guppy programs into MLIR objects."""


from enum import Enum
from pathlib import Path
from tempfile import TemporaryFile


class MlirMode(Enum):
    """The output format for the MLIR object."""

    BITCODE = 0
    TEXTUAL = 1


def hugr_to_mlir(hugr_json: Path, mlir_out: Path | None, mode: MlirMode) -> Path:
    """Compile the input Hugr json encoding a Guppy program into a LLVMIR object.

    ## Parameters
    hugr_json: Path
        The path to the input Hugr json file.
    mlir_out: Path | None
        The path to the output file.
    textual: bool
        Whether to produce textual LLVMIR instead of bitcode.

    ## Returns
    Returns the path to the output file.
    """
    mlir_out: Path = mlir_out or Path(
        TemporaryFile(mode="w", prefix="mlir_", suffix=".mlir"),
    )

    _ = (hugr_json, mlir_out, mode)
    raise NotImplementedError
