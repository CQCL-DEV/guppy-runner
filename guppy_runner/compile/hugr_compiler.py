"""Methods for compiling HUGR-encoded guppy programs into MLIR objects."""


import os
import subprocess
from pathlib import Path
from subprocess import CalledProcessError

from guppy_runner.compile import CompilerError, StageCompiler, UnsupportedEncodingError
from guppy_runner.stage import EncodingMode, Stage
from guppy_runner.util import LOGGER

HUGR_MLIR_TRANSLATE = "hugr-mlir-translate"
HUGR_MLIR_TRANSLATE_ENV = "HUGR_MLIR_TRANSLATE"


class HugrCompiler(StageCompiler):
    """A processor for compiling Hugr objects into MLIR."""

    INPUT_STAGE: Stage = Stage.HUGR
    OUTPUT_STAGE: Stage = Stage.HUGR_MLIR

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
        """Execute `hugr-mlir-translate`."""
        _ = output_path, temp_file, module_name

        if output_encoding == EncodingMode.BITCODE:
            raise UnsupportedEncodingError(self.OUTPUT_STAGE, output_encoding)

        output_as_text = output_encoding == EncodingMode.TEXTUAL
        input_mode_flag = (
            "--hugr-json-to-mlir"
            if input_encoding == EncodingMode.TEXTUAL
            else "--hugr-rmp-to-mlir"
        )
        cmd = [self._get_compiler()[0], input_mode_flag, input_path]

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
            raise HugrMlirTranslateNotFoundError(*self._get_compiler()) from err
        except CalledProcessError as err:
            raise MlirTranslateError(err) from err

        # TODO: Temporary fix. `hugr-mlir-translate` is not marking main as public.
        return str(completed.stdout).replace(
            "func @main",
            "func public @main",
        )

    def _get_compiler(self) -> tuple[Path, bool]:
        """Returns the path to the `hugr-mlir-translate` binary.

        Looks for it in your PATH by default, unless a "HUGR_MLIR_TRANSLATE" env
        variable is set.

        The returned boolean indicates whether the path was overridden via the
        environment variable.
        """
        if HUGR_MLIR_TRANSLATE_ENV in os.environ:
            return (Path(os.environ[HUGR_MLIR_TRANSLATE_ENV]), True)
        return (Path(HUGR_MLIR_TRANSLATE), False)


class HugrCompilerError(CompilerError):
    """Base class for Hugr compiler errors."""


class HugrMlirTranslateNotFoundError(HugrCompilerError):
    """Raised when the translation program cannot be found."""

    def __init__(self, path: Path, bin_from_path: bool) -> None:  # noqa: FBT001
        """Initialize the error."""
        if not bin_from_path:
            super().__init__(
                f"Could not find '{HUGR_MLIR_TRANSLATE}' binary in your $PATH. "
                f"You can set an explicit path with the {HUGR_MLIR_TRANSLATE_ENV} env "
                "variable.",
            )
        else:
            super().__init__(
                f"Could not find 'hugr-mlir-translate' binary in '{path}', set via the "
                f"{HUGR_MLIR_TRANSLATE_ENV} env variable.",
            )


class MlirTranslateError(HugrCompilerError):
    """Raised when the translation program cannot be found."""

    def __init__(self, perror: CalledProcessError) -> None:
        """Initialize the error."""
        err_line = next(iter(perror.stderr.splitlines()), "")
        super().__init__(
            f"An error occurred while calling 'hugr-mlir-translate':\n{err_line}",
        )
