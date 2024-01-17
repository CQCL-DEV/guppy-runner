"""Utilities to link and run the final LLVM artifact."""


import os
import subprocess
from pathlib import Path
from subprocess import CalledProcessError

from guppy_runner.compile import (
    CompilerError,
    StageCompiler,
    UnsupportedEncodingError,
)
from guppy_runner.stage import EncodingMode, Stage
from guppy_runner.util import LOGGER

CLANG = "clang"
QIR_BACKEND_LIBS_ENV = "QIR_BACKEND_LIBS"

# TODO: Find the way to use a temporary file that gets deleted afterwards.
DEFAULT_BIN = Path("a.out")


class Linker(StageCompiler):
    """A processor for linking object files into binaries."""

    INPUT_STAGE: Stage = Stage.OBJECT
    OUTPUT_STAGE: Stage = Stage.EXECUTABLE

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
        """Compile the LLVMIR artifact into a runnable program."""
        _ = input_path, input_encoding, output_encoding, temp_file, module_name

        if output_encoding == EncodingMode.TEXTUAL:
            raise UnsupportedEncodingError(self.OUTPUT_STAGE, output_encoding)

        if not output_path:
            output_path = DEFAULT_BIN

        cmd = [
            self._get_compiler()[0],
            input_path,
            "-o",
            output_path,
            "-L",
            self._get_qir_lib_path(),
            "-lqir_backend",
            "-lm",
        ]

        cmd_str = " ".join(str(c) for c in cmd)
        msg = f"Executing command: '{cmd_str}'"
        LOGGER.info(msg)
        try:
            subprocess.run(
                cmd,  # noqa: S603
                capture_output=True,
                check=True,
                text=False,
            )
        except FileNotFoundError as err:
            raise ClangNotFoundError from err
        except CalledProcessError as err:
            raise ClangError(err) from err

        return output_path

    def _get_compiler(self) -> tuple[Path, bool]:
        """Returns the path to the `clang` binary.

        The returned boolean indicates whether the path was overridden via the
        environment variable.
        """
        return (Path(CLANG), False)

    def _get_qir_lib_path(self) -> Path:
        """Returns the path to the QIR library.

        This must contain the `qir_backend` library to link to.

        This path **must** be set via the QIR_BACKEND_LIBS environment variable.
        """
        try:
            return Path(os.environ[QIR_BACKEND_LIBS_ENV])
        except KeyError:
            raise QirLibsNotSetError from None


class LinkerError(CompilerError):
    """Base class for Hugr compiler errors."""


class QirLibsNotSetError(LinkerError):
    """Raised when the QIR libs path has not been set."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__(
            "You must set the qir_backend libs path as the "
            f"'{QIR_BACKEND_LIBS_ENV}' environment variable.",
        )


class ClangNotFoundError(LinkerError):
    """Raised when the translation program cannot be found."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__(f"Could not find '{CLANG}' binary in your $PATH.")


class ClangError(LinkerError):
    """Raised when the translation program cannot be found."""

    def __init__(self, perror: CalledProcessError) -> None:
        """Initialize the error."""
        err_line = next(iter(perror.stderr.splitlines()), "")
        super().__init__(
            f"An error occurred while calling '{CLANG}':\n{err_line}",
        )
