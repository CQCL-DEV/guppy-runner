"""Methods for compiling Guppy programs into HUGRs."""

import importlib.machinery
import types
from pathlib import Path
from tempfile import NamedTemporaryFile

from guppy.module import GuppyModule  # type: ignore

from guppy_runner.workflow import EncodingMode, Stage, StageData, StageProcessor


def guppy_to_hugr(guppy: Path, hugr_out: Path | None) -> Path:
    """Compile the input Guppy program into a msgpack-encoded Hugr.

    If `hugr_out` is `None`, then a temporary file is created.
    Note that the temporary file is not deleted.

    Returns the path to the msgpack file.
    """
    input_data = StageData(Stage.GUPPY, guppy, EncodingMode.BITCODE)
    output = GuppyCompiler().run(input_data, hugr_out=hugr_out)
    return output.file_path


class GuppyCompiler(StageProcessor):
    """A processor for compiling Guppy programs into Hugrs."""

    INPUT_STAGE: Stage = Stage.GUPPY
    OUTPUT_STAGE: Stage = Stage.HUGR

    def run(self, data: StageData, *, hugr_out: Path | None, **kwargs) -> StageData:
        """Transform the input into the following stage."""
        assert not kwargs

        if data.stage != self.INPUT_STAGE:
            err = f"Invalid input stage {data.stage}."
            raise ValueError(err)

        if hugr_out is None:
            out_encoding = EncodingMode.BITCODE
        else:
            out_encoding = (
                EncodingMode.from_file(hugr_out, Stage.HUGR) or EncodingMode.BITCODE
            )

        module = self._load_module(data.file_path)
        hugr = module.compile()
        if out_encoding == EncodingMode.TEXTUAL:
            serial_hugr = hugr.serialize_json()
        else:
            serial_hugr = hugr.serialize()

        if hugr_out:
            mode = "w" if out_encoding == EncodingMode.TEXTUAL else "wb"
            with hugr_out.open(mode=mode) as hugr_file:
                hugr_file.write(serial_hugr)
        else:
            with NamedTemporaryFile(
                mode="wb",
                prefix="hugr_",
                suffix=".msgpack",
                delete=False,
            ) as hugr_file:
                hugr_out = Path(hugr_file.name)
                hugr_file.write(serial_hugr)

        return StageData(Stage.HUGR, hugr_out, out_encoding)

    def _load_module(self, guppy: Path) -> GuppyModule:
        """Load the input Guppy program as a Python module."""
        loader = importlib.machinery.SourceFileLoader("main", str(guppy))
        py_module = types.ModuleType(loader.name)
        try:
            loader.exec_module(py_module)
        except FileNotFoundError as err:
            raise InvalidGuppyModuleError(guppy) from err

        if "main" not in py_module.__dir__():
            raise MissingMainError(guppy)
        if not isinstance(py_module.main, GuppyModule):
            raise NotAGuppyError(guppy)

        return py_module.main


class GuppyCompilerError(Exception):
    """Base class for Guppy compiler errors."""


class InvalidGuppyModuleError(GuppyCompilerError):
    """Raised when a Guppy program path is invalid."""

    def __init__(self, guppy: Path) -> None:
        """Initialize the error."""
        super().__init__(f"Invalid Guppy module path '{guppy}'.")


class MissingMainError(GuppyCompilerError):
    """Raised when a Guppy program cannot be loaded."""

    def __init__(self, guppy: Path) -> None:
        """Initialize the error."""
        super().__init__(f"Guppy program {guppy} does not define a main function.")


class NotAGuppyError(GuppyCompilerError):
    """Raised when a the program is not a GuppyModule."""

    def __init__(self, guppy: Path) -> None:
        """Initialize the error."""
        super().__init__(f"Module {guppy} does not define a `main` GuppyModule.")
