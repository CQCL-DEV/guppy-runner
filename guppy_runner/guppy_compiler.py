"""Methods for compiling Guppy programs into HUGRs."""

__all__ = [
    "guppy_to_hugr",
    "GuppyCompilerError",
    "MissingMainError",
    "NotAGuppyError",
]

import importlib.machinery
import types
from pathlib import Path
from tempfile import NamedTemporaryFile

from guppy.module import GuppyModule


def guppy_to_hugr(guppy: Path, hugr_out: Path | None) -> Path:
    """Compile the input Guppy program into a msgpack-encoded Hugr.

    If `hugr_out` is `None`, then a temporary file is created.
    Note that the temporary file is not deleted.

    Returns the path to the msgpack file.
    """
    module = _load_module(guppy)
    hugr = module.compile()
    serial_hugr = hugr.serialize()

    if hugr_out:
        with hugr_out.open(mode="wb") as hugr_file:
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

    return hugr_out


def _load_module(guppy: Path) -> GuppyModule:
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
