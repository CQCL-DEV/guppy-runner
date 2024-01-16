"""Methods for producing runnable artifacts from MLIR objects."""


import os
import subprocess
from pathlib import Path
from subprocess import CalledProcessError

from guppy_runner.compile import CompilerError, StageCompiler
from guppy_runner.stage import EncodingMode, Stage
from guppy_runner.util import LOGGER

HUGR_MLIR_OPT = "hugr-mlir-opt"
HUGR_MLIR_OPT_ENV = "HUGR_MLIR_OPT"


class MLIRLowerer(StageCompiler):
    """A processor for lowering hugr MLIR into the LLVM dialect."""

    INPUT_STAGE: Stage = Stage.HUGR_MLIR
    OUTPUT_STAGE: Stage = Stage.LOWERED_MLIR

    def process_stage(  # noqa: PLR0913
        self,
        *,
        input_path: Path,
        input_encoding: EncodingMode,
        output_encoding: EncodingMode,
        temp_file: bool = False,
        module_name: str | None = None,
    ) -> str | bytes:
        """Execute `hugr-mlir-opt`."""
        _ = input_encoding, temp_file, module_name

        output_as_text = output_encoding == EncodingMode.TEXTUAL
        cmd = [self._get_compiler()[0], input_path, "--lower-hugr"]
        if not output_as_text:
            cmd += ["--emit-bytecode"]

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
            raise MlirLowererTranslateNotFoundError(*self._get_compiler()) from err
        except CalledProcessError as err:
            raise MlirOptError(err) from err
        return completed.stdout

    def _get_compiler(self) -> tuple[Path, bool]:
        """Returns the path to the `hugr-mlir-opt` binary.

        Looks for it in your PATH by default, unless a "HUGR_MLIR_OPT" env
        variable is set.

        The returned boolean indicates whether the path was overridden via the
        environment variable.
        """
        if HUGR_MLIR_OPT_ENV in os.environ:
            return (Path(os.environ[HUGR_MLIR_OPT_ENV]), True)
        return (Path(HUGR_MLIR_OPT), False)


class MlirLowererError(CompilerError):
    """Base class for Mlir compiler errors."""


class MlirLowererTranslateNotFoundError(MlirLowererError):
    """Raised when the translation program cannot be found."""

    def __init__(self, path: Path, bin_from_path: bool) -> None:  # noqa: FBT001
        """Initialize the error."""
        if not bin_from_path:
            super().__init__(
                f"Could not find 'hugr-mlir-opt' binary in your $PATH. "
                f"You can set an explicit path with the {HUGR_MLIR_OPT_ENV} env "
                "variable.",
            )
        else:
            super().__init__(
                f"Could not find 'hugr-mlir-opt' binary in '{path}', set via the "
                f"{HUGR_MLIR_OPT_ENV} env variable.",
            )


class MlirOptError(MlirLowererError):
    """Raised when the translation program cannot be found."""

    def __init__(self, perror: CalledProcessError) -> None:
        """Initialize the error."""
        err_line = next(iter(perror.stderr.splitlines()), "")
        super().__init__(
            f"An error occurred while calling 'hugr-mlir-opt':\n{err_line}",
        )
