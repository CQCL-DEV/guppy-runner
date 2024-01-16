"""Methods for producing runnable artifacts from MLIR objects."""


import os
import subprocess
from pathlib import Path
from subprocess import CalledProcessError

from guppy_runner.compile import CompilerError, StageCompiler, UnsupportedEncodingError
from guppy_runner.stage import EncodingMode, Stage
from guppy_runner.util import LOGGER

MLIR_TRANSLATE = "mlir-translate"
MLIR_TRANSLATE_ENV = "MLIR_TRANSLATE"


class MLIRCompiler(StageCompiler):
    """A processor for compiling lowered MLIR objects into LLVMIR."""

    INPUT_STAGE: Stage = Stage.LOWERED_MLIR
    OUTPUT_STAGE: Stage = Stage.LLVM

    def process_stage(  # noqa: PLR0913
        self,
        *,
        input_path: Path,
        input_encoding: EncodingMode,
        output_encoding: EncodingMode,
        temp_file: bool = False,
        module_name: str | None = None,
    ) -> str | bytes:
        """Execute `mlir-translate`."""
        _ = input_encoding, temp_file, module_name

        if output_encoding == EncodingMode.BITCODE:
            raise UnsupportedEncodingError(self.OUTPUT_STAGE, output_encoding)

        output_as_text = output_encoding == EncodingMode.TEXTUAL
        cmd = [self._get_compiler()[0], input_path, "--mlir-to-llvmir"]

        cmd_str = " ".join(str(c) for c in cmd)
        msg = f"Executing command: '{cmd_str}'"
        LOGGER.info(msg)
        try:
            completed = subprocess.run(
                cmd,  # noqa: S603
                capture_output=True,
                check=True,
                text=output_as_text,
            )
        except FileNotFoundError as err:
            raise MlirTranslateNotFoundError(*self._get_compiler()) from err
        except CalledProcessError as err:
            raise MlirTranslateError(err) from err
        return completed.stdout

    def _get_compiler(self) -> tuple[Path, bool]:
        """Returns the path to the `mlir-translate` binary.

        Looks for it in your PATH by default, unless a "MLIR_TRANSLATE" env
        variable is set.

        The returned boolean indicates whether the path was overridden via the
        environment variable.
        """
        if MLIR_TRANSLATE_ENV in os.environ:
            return (Path(os.environ[MLIR_TRANSLATE_ENV]), True)
        return (Path(MLIR_TRANSLATE), False)


class MlirCompilerError(CompilerError):
    """Base class for Mlir compiler errors."""


class MlirTranslateNotFoundError(MlirCompilerError):
    """Raised when the translation program cannot be found."""

    def __init__(self, path: Path, bin_from_path: bool) -> None:  # noqa: FBT001
        """Initialize the error."""
        if not bin_from_path:
            super().__init__(
                f"Could not find '{MLIR_TRANSLATE}' binary in your $PATH. "
                f"You can set an explicit path with the {MLIR_TRANSLATE_ENV} env "
                "variable.",
            )
        else:
            super().__init__(
                f"Could not find '{MLIR_TRANSLATE}' binary in '{path}', set via the "
                f"{MLIR_TRANSLATE_ENV} env variable.",
            )


class MlirTranslateError(MlirCompilerError):
    """Raised when the translation program cannot be found."""

    def __init__(self, perror: CalledProcessError) -> None:
        """Initialize the error."""
        err_line = next(iter(perror.stderr.splitlines()), "")
        super().__init__(
            f"An error occurred while calling '{MLIR_TRANSLATE}':\n{err_line}",
        )
