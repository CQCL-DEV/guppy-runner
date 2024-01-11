"""Methods for compiling Guppy programs into HUGRs."""

import importlib.machinery
import tempfile
import types
from pathlib import Path

from guppy.module import GuppyModule  # type: ignore

from guppy_runner.workflow import (
    EncodingMode,
    ProcessorError,
    Stage,
    StageData,
    StageProcessor,
)


def guppy_to_hugr(
    guppy: str | bytes,
    output_mode: EncodingMode = EncodingMode.TEXTUAL,
) -> str | bytes:
    """Compile the input Guppy program into a msgpack-encoded Hugr.

    If `hugr_out` is `None`, then a temporary file is created.
    Note that the temporary file is not deleted.

    Returns the path to the msgpack file.
    """
    encoding = EncodingMode.from_data(guppy)
    input_data = StageData.from_path(Stage.GUPPY, guppy, encoding)
    output = GuppyCompiler().run(input_data, output_mode=output_mode)
    return output.data


class GuppyCompiler(StageProcessor):
    """A processor for compiling Guppy programs into Hugrs."""

    INPUT_STAGE: Stage = Stage.GUPPY
    OUTPUT_STAGE: Stage = Stage.HUGR

    def run(
        self,
        data: StageData,
        *,
        hugr_out: Path | None = None,
        output_mode: EncodingMode | None = None,
        **kwargs,
    ) -> StageData:
        """Transform the input into the following stage."""
        assert not kwargs
        self._check_stage(data)

        # Determine the output encoding.
        if output_mode is None and hugr_out is None:
            output_mode = EncodingMode.BITCODE
        elif output_mode is None:
            output_mode = (
                EncodingMode.from_file(hugr_out, Stage.HUGR) or EncodingMode.BITCODE
            )

        # Load the Guppy program and compile it.
        if data.data_path is None:
            module = self._load_guppy_string(data.data)
        elif data.encoding == EncodingMode.TEXTUAL:
            module = self._load_guppy_file(data.data_path)
        else:
            raise BitcodeProgramError
        hugr = module.compile()

        # Serialize the Hugr artifact.
        if output_mode == EncodingMode.TEXTUAL:
            serial_hugr = hugr.serialize_json()
        else:
            serial_hugr = hugr.serialize()

        # Write the Hugr if requested.
        if hugr_out:
            mode = "w" if output_mode == EncodingMode.TEXTUAL else "wb"
            with hugr_out.open(mode=mode) as hugr_file:
                hugr_file.write(serial_hugr)

        return StageData(Stage.HUGR, serial_hugr, output_mode)

    def _load_guppy_string(self, program: str) -> types.ModuleType:
        """Load a Guppy file as a Python module, and return it."""
        # Guppy needs the program to have an associated source,
        # so we need to create a temporary file.
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
        ) as temp_file:
            temp_file.write(program)
            program_path = Path(temp_file.name)
        module = self._load_guppy_file(program_path, temp_file=True)
        # Delete the temporary file.
        program_path.unlink()
        return module

    def _load_guppy_file(
        self,
        program_path: Path,
        *,
        temp_file: bool = False,
    ) -> GuppyModule:
        """Load a Guppy file as a Python module, and return it."""
        loader = importlib.machinery.SourceFileLoader("main", str(program_path))
        py_module = types.ModuleType(loader.name)
        try:
            loader.exec_module(py_module)
        except FileNotFoundError as err:
            raise InvalidGuppyModulePathError(program_path) from err
        return self._get_main(py_module, program_path if not temp_file else None)

    def _get_main(
        self,
        py_module: types.ModuleType,
        source_path: Path | None,
    ) -> GuppyModule:
        if "main" not in py_module.__dir__():
            raise MissingMainError(source_path)
        if not isinstance(py_module.main, GuppyModule):
            raise NotAGuppyError(source_path)

        return py_module.main


class GuppyCompilerError(ProcessorError):
    """Base class for Guppy compiler errors."""


class BitcodeProgramError(GuppyCompilerError):
    """Raised when a in-memory program is not string.

    We do not support in-memory bitcode programs.
    """

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__("In-memory guppy programs must be strings.")


class InvalidGuppyModulePathError(GuppyCompilerError):
    """Raised when a Guppy program path is invalid."""

    def __init__(self, guppy: Path) -> None:
        """Initialize the error."""
        super().__init__(f"Invalid Guppy module path '{guppy}'.")


class MissingMainError(GuppyCompilerError):
    """Raised when a Guppy program cannot be loaded."""

    def __init__(self, guppy: Path | None) -> None:
        """Initialize the error."""
        if guppy is None:
            super().__init__("Program does not define a main module.")
        else:
            super().__init__(f"Guppy program {guppy} does not define a main module.")


class NotAGuppyError(GuppyCompilerError):
    """Raised when a the program is not a GuppyModule."""

    def __init__(self, guppy: Path | None) -> None:
        """Initialize the error."""
        if guppy is None:
            super().__init__("`main` must be a GuppyModule.")
        else:
            super().__init__(f"`main` in program {guppy} must be a GuppyModule.")
