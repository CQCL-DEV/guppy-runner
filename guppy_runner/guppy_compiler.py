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
        module_name: str | None = None,
        **kwargs,
    ) -> StageData:
        """Transform the input into the following stage."""
        _ = kwargs
        self._check_stage(data)

        # Determine the output encoding.
        if output_mode is None:
            if hugr_out is None:
                output_mode = EncodingMode.BITCODE
            else:
                output_mode = (
                    EncodingMode.from_file(hugr_out, Stage.HUGR) or EncodingMode.BITCODE
                )

        # Load the Guppy program and compile it.
        if data.data_path is None:
            # In-memory guppy programs are always strings.
            assert isinstance(data.data, str)
            module = self._load_guppy_string(data.data, module_name=module_name)
        elif data.encoding == EncodingMode.TEXTUAL:
            module = self._load_guppy_file(data.data_path, module_name=module_name)
        else:
            raise BitcodeProgramError
        hugr = module.compile()

        # Serialize the Hugr artifact.
        if output_mode == EncodingMode.TEXTUAL:
            serial_hugr = hugr.serialize_json()
        else:
            serial_hugr = hugr.serialize()

        out_data = StageData(Stage.HUGR, serial_hugr, output_mode)

        # Write the Hugr if requested.
        if hugr_out:
            self._store_artifact(out_data, hugr_out)

        return out_data

    def _load_guppy_string(
        self,
        program: str,
        module_name: str | None = None,
    ) -> types.ModuleType:
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
        module = self._load_guppy_file(
            program_path,
            module_name=module_name,
            temp_file=True,
        )
        # Delete the temporary file.
        program_path.unlink()
        return module

    def _load_guppy_file(
        self,
        program_path: Path,
        *,
        module_name: str | None = None,
        temp_file: bool = False,
    ) -> GuppyModule:
        """Load a Guppy file as a Python module, and return it."""
        loader = importlib.machinery.SourceFileLoader("module", str(program_path))
        py_module = types.ModuleType(loader.name)
        try:
            loader.exec_module(py_module)
        except FileNotFoundError as err:
            raise InvalidGuppyModulePathError(program_path) from err
        return self._get_module(
            py_module,
            program_path if not temp_file else None,
            module_name=module_name,
        )

    def _get_module(
        self,
        py_module: types.ModuleType,
        source_path: Path | None,
        module_name: str | None = None,
    ) -> GuppyModule:
        # TODO: Using a default module requires fixing `set_module` first.
        # https://github.com/CQCL-DEV/guppy/issues/101
        module_name = module_name or "module"

        if module_name:
            if module_name not in py_module.__dir__():
                raise MissingModuleError(module_name, source_path)
            module = getattr(py_module, module_name)
        else:
            raise NotImplementedError

        if not isinstance(module, GuppyModule):
            assert module_name is not None
            raise NotAGuppyError(source_path)
        if not module.contains_function("main"):
            raise MissingMainError(module_name, source_path)

        return module


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


class MissingModuleError(GuppyCompilerError):
    """Raised when a Guppy program cannot be loaded."""

    def __init__(self, module: str, guppy: Path | None) -> None:
        """Initialize the error."""
        if guppy is None:
            super().__init__(f"The Guppy program does not define a `{module}` module.")
        else:
            super().__init__(
                f"The Guppy program {guppy} does not define a `{module}` module.",
            )


class MissingMainError(GuppyCompilerError):
    """Raised when a Guppy program cannot be loaded."""

    def __init__(self, module: str, guppy: Path | None) -> None:
        """Initialize the error."""
        if guppy is None:
            super().__init__(
                f"The `{module}` module in the Guppy program does not define a main "
                "function.",
            )
        else:
            super().__init__(
                f"The `{module}` module in Guppy program {guppy} does not "
                "define a main function.",
            )


class NotAGuppyError(GuppyCompilerError):
    """Raised when a the program is not a GuppyModule."""

    def __init__(self, guppy: Path | None) -> None:
        """Initialize the error."""
        if guppy is None:
            super().__init__("`main` must be a GuppyModule.")
        else:
            super().__init__(f"`main` in program {guppy} must be a GuppyModule.")
