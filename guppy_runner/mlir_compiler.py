"""Methods for producing runnable artifacts from MLIR objects."""


import os
import subprocess
import tempfile
from pathlib import Path
from subprocess import CalledProcessError

from guppy_runner.util import LOGGER
from guppy_runner.workflow import (
    EncodingMode,
    ProcessorError,
    Stage,
    StageData,
    StageProcessor,
)

HUGR_MLIR_OPT = "hugr-mlir-opt"
HUGR_MLIR_OPT_ENV = "HUGR_MLIR_OPT"


class MLIRCompiler(StageProcessor):
    """A processor for compiling MLIR objects into LLVMIR."""

    INPUT_STAGE: Stage = Stage.MLIR
    OUTPUT_STAGE: Stage = Stage.LLVM

    def run(self, data: StageData, *, llvm_out: Path | None, **kwargs) -> StageData:
        """Transform the input into the following stage."""
        _ = kwargs
        self._check_stage(data)

        # TODO: Support bitcode LLVMIR output
        output_mode = EncodingMode.TEXTUAL

        # Compile the MLIR.
        if data.data_path is None:
            llvm = self._compile_hugr_data(data.data, data.encoding, output_mode)
        else:
            llvm = self._compile_hugr_file(data.data_path, data.encoding, output_mode)

        out_data = StageData(Stage.LLVM, llvm, output_mode)

        # Write the llvm file if requested.
        if llvm_out:
            self._store_artifact(out_data, llvm_out)

        return out_data

    def _compile_hugr_data(
        self,
        hugr: str | bytes,
        input_encoding: EncodingMode,
        output_encoding: EncodingMode,
    ) -> str | bytes:
        """Compile a serialized MLIR into LLVMIR."""
        # hugr-mlir-opt requires an input file.
        mode = "w" if input_encoding == EncodingMode.TEXTUAL else "wb"
        with tempfile.NamedTemporaryFile(
            mode=mode,
            suffix=".mlir",
            delete=False,
        ) as temp_file:
            temp_file.write(hugr)
            hugr_path = Path(temp_file.name)
        llvm = self._exec_translate(hugr_path, input_encoding, output_encoding)
        hugr_path.unlink()
        return llvm

    def _compile_hugr_file(
        self,
        path: Path,
        input_encoding: EncodingMode,
        output_encoding: EncodingMode,
    ) -> str | bytes:
        """Compile a MLIR file into LLVMIR."""
        return self._exec_translate(path, input_encoding, output_encoding)

    def _exec_translate(
        self,
        input_path: Path,
        input_encoding: EncodingMode,
        output_encoding: EncodingMode,
    ) -> str | bytes:
        """Execute the `mlir-opt` command."""
        assert (
            input_encoding == EncodingMode.TEXTUAL
        ), "Bitcode MLIR is not supported yet"
        output_as_text = output_encoding == EncodingMode.TEXTUAL
        cmd = [self._get_compiler()[0], input_path, "--lower-hugr"]
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
            raise MlirLlvmTranslateNotFoundError(*self._get_compiler()) from err
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


class MlirCompilerError(ProcessorError):
    """Base class for Mlir compiler errors."""


class MlirLlvmTranslateNotFoundError(MlirCompilerError):
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


class MlirOptError(MlirCompilerError):
    """Raised when the translation program cannot be found."""

    def __init__(self, perror: CalledProcessError) -> None:
        """Initialize the error."""
        err_line = next(iter(perror.stderr.splitlines()), "")
        super().__init__(
            f"An error occurred while calling 'hugr-mlir-opt':\n{err_line}",
        )
