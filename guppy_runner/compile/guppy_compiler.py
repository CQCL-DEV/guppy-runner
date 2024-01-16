"""Methods for compiling Guppy programs into HUGRs."""

import importlib.machinery
import types
from pathlib import Path

from guppy.module import GuppyModule  # type: ignore

from guppy_runner.compile import CompilerError, StageCompiler
from guppy_runner.stage import EncodingMode, Stage


class GuppyCompiler(StageCompiler):
    """A processor for compiling Guppy programs into Hugrs."""

    INPUT_STAGE: Stage = Stage.GUPPY
    OUTPUT_STAGE: Stage = Stage.HUGR

    def process_stage(  # noqa: PLR0913
        self,
        *,
        input_path: Path,
        input_encoding: EncodingMode,
        output_path: Path | None,
        output_encoding: EncodingMode,
        temp_file: bool = False,
        module_name: str | None = None,
    ) -> str | bytes:
        """Load a Guppy file as a Python module, and return it."""
        _ = output_path
        if input_encoding != EncodingMode.TEXTUAL:
            raise BitcodeProgramError

        loader = importlib.machinery.SourceFileLoader("module", str(input_path))
        py_module = types.ModuleType(loader.name)
        try:
            loader.exec_module(py_module)
        except FileNotFoundError as err:
            raise InvalidGuppyModulePathError(input_path) from err

        module = self._get_module(
            py_module,
            input_path if not temp_file else None,
            module_name=module_name,
        )
        hugr = module.compile()

        # Serialize the Hugr artifact.
        if output_encoding == EncodingMode.TEXTUAL:
            return hugr.serialize_json()
        return hugr.serialize()

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


class GuppyCompilerError(CompilerError):
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
