"""Tests for the public API."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from guppylang.decorator import guppy  # type: ignore
from guppylang.module import GuppyModule  # type: ignore

from guppy_runner import run_guppy, run_guppy_module

EVEN_ODD: Path = Path("test_files/even_odd.py")


def test_even_odd():
    with NamedTemporaryFile(suffix=".hugr") as temp_hugr, NamedTemporaryFile(
        suffix=".mlir",
    ) as temp_mlir, NamedTemporaryFile(
        suffix=".mlir",
    ) as temp_lower_mlir, NamedTemporaryFile(
        suffix=".ll",
    ) as temp_llvm, NamedTemporaryFile(
        suffix=".o",
    ) as temp_obj, NamedTemporaryFile(
        suffix=".out",
    ) as temp_bin:
        temp_hugr.close()
        temp_mlir.close()
        temp_lower_mlir.close()
        temp_llvm.close()
        temp_obj.close()
        temp_bin.close()

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
            obj_out=Path(temp_obj.name),
            bin_out=Path(temp_bin.name),
            no_run=True,
        )


def test_from_module():
    module = GuppyModule("my_module")

    @guppy(module)
    def main() -> bool:
        return True

    with NamedTemporaryFile(suffix=".o") as temp_obj, NamedTemporaryFile(
        suffix=".out",
    ) as temp_bin:
        temp_obj.close()
        temp_bin.close()

        # Just check that it runs.
        #
        # We cannot load any of the artifacts with just the guppy library,
        # so we have to assume that they are correct.
        assert run_guppy_module(
            module,
            obj_out=Path(temp_obj.name),
            bin_out=Path(temp_bin.name),
            no_run=True,
        )
