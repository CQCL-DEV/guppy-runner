"""Methods for compiling HUGR-encoded guppy programs into MLIR objects."""


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

HUGR_MLIR_TRANSLATE = "hugr-mlir-translate"
HUGR_MLIR_TRANSLATE_ENV = "HUGR_MLIR_TRANSLATE"


class HugrCompiler(StageProcessor):
    """A processor for compiling Hugr objects into MLIR."""

    INPUT_STAGE: Stage = Stage.HUGR
    OUTPUT_STAGE: Stage = Stage.MLIR

    def run(self, data: StageData, *, mlir_out: Path | None, **kwargs) -> StageData:
        """Transform the input into the following stage."""
        _ = kwargs
        self._check_stage(data)

        # TODO: Support bitcode MLIR output
        output_mode = EncodingMode.TEXTUAL

        # Compile the Hugr.
        if data.data_path is None:
            mlir = self._compile_hugr_data(data.data, data.encoding, output_mode)
        else:
            mlir = self._compile_hugr_file(data.data_path, data.encoding, output_mode)

        out_data = StageData(Stage.MLIR, mlir, output_mode)

        # Write the mlir file if requested.
        if mlir_out:
            self._store_artifact(out_data, mlir_out)

        return out_data

    def _compile_hugr_data(
        self,
        hugr: str | bytes,
        input_encoding: EncodingMode,
        output_encoding: EncodingMode,
    ) -> str | bytes:
        """Compile a serialized Hugr into MLIR."""
        # hugr-mlir-translate requires an input file.
        mode = "w" if input_encoding == EncodingMode.TEXTUAL else "wb"
        suffix = ".json" if input_encoding == EncodingMode.TEXTUAL else ".msgpack"
        with tempfile.NamedTemporaryFile(
            mode=mode,
            suffix=suffix,
            delete=False,
        ) as temp_file:
            temp_file.write(hugr)
            hugr_path = Path(temp_file.name)
        mlir = self._exec_translate(hugr_path, input_encoding, output_encoding)
        hugr_path.unlink()
        return mlir

    def _compile_hugr_file(
        self,
        path: Path,
        input_encoding: EncodingMode,
        output_encoding: EncodingMode,
    ) -> str | bytes:
        """Compile a Hugr file into MLIR."""
        return self._exec_translate(path, input_encoding, output_encoding)

    def _exec_translate(
        self,
        input_path: Path,
        input_encoding: EncodingMode,
        output_encoding: EncodingMode,
    ) -> str | bytes:
        """Execute the `mlir-translate` command."""
        input_mode_flag = (
            "--hugr-json-to-mlir"
            if input_encoding == EncodingMode.TEXTUAL
            else "--hugr-rmp-to-mlir"
        )
        output_as_text = output_encoding == EncodingMode.TEXTUAL
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

        return completed.stdout

    def _get_compiler(self) -> (Path, bool):
        """Returns the path to the `hugr-mlir-translate` binary.

        Looks for it in your PATH by default, unless a "HUGR_MLIR_TRANSLATE" env
        variable is set.

        The returned boolean indicates whether the path was overridden via the
        environment variable.
        """
        if HUGR_MLIR_TRANSLATE_ENV in os.environ:
            return (Path(os.environ[HUGR_MLIR_TRANSLATE_ENV]), True)
        return (Path(HUGR_MLIR_TRANSLATE), False)


class HugrCompilerError(ProcessorError):
    """Base class for Hugr compiler errors."""


class HugrMlirTranslateNotFoundError(HugrCompilerError):
    """Raised when the translation program cannot be found."""

    def __init__(self, path: Path, bin_from_path: bool) -> None:  # noqa: FBT001
        """Initialize the error."""
        if not bin_from_path:
            super().__init__(
                f"Could not find 'hugr-mlir-translate' binary in your $PATH. "
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
