"""Tests for the public API."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from guppy.decorator import guppy  # type: ignore
from guppy.module import GuppyModule  # type: ignore

from guppy_runner import run_guppy, run_guppy_module

EVEN_ODD: Path = Path("test_files/even_odd.py")


def test_even_odd():
    with NamedTemporaryFile(suffix=".hugr") as temp_hugr, NamedTemporaryFile(
        suffix=".mlir",
    ) as temp_mlir, NamedTemporaryFile(
        suffix=".mlir",
    ) as temp_lower_mlir, NamedTemporaryFile(
        suffix=".ll",
    ) as temp_llvm:
        temp_hugr.close()
        temp_mlir.close()
        temp_lower_mlir.close()
        temp_llvm.close()

        # Just check that it runs.
        #
        # We cannot load any of the artifacts with just the guppy library,
        # so we have to assume that they are correct.
        assert run_guppy(
            EVEN_ODD,
            hugr_out=Path(temp_hugr.name),
            hugr_mlir_out=Path(temp_mlir.name),
            lowered_mlir_out=Path(temp_lower_mlir.name),
            llvm_out=Path(temp_llvm.name),
            no_run=True,
        )


def test_from_module():
    module = GuppyModule("module")

    @guppy(module)
    def main(x: bool) -> bool:  # noqa: FBT001
        return x

    with NamedTemporaryFile(suffix=".ll") as temp_llvm:
        temp_llvm.close()

        # Just check that it runs.
        #
        # We cannot load any of the artifacts with just the guppy library,
        # so we have to assume that they are correct.
        assert run_guppy_module(
            module,
            llvm_out=Path(temp_llvm.name),
            no_run=True,
        )
