"""Utilities to link and run the final LLVM artifact."""


from pathlib import Path

from guppy_runner.compile import (
    CompilerError,
    InvalidStageError,
    StageCompiler,
    UnsupportedEncodingError,
)
from guppy_runner.stage import (
    EncodingMode,
    Stage,
    StageData,
)


def run_artifact(artifact: StageData) -> None:
    """Link the LLVM artifact and run it."""
    _ = artifact
    if artifact.stage != Stage.LLVM:
        raise InvalidStageError(artifact.stage, Stage.LLVM)

    raise NotImplementedError


class Runner(StageCompiler):
    """A processor for running an LLVMIR artifact."""

    INPUT_STAGE: Stage = Stage.LLVM
    OUTPUT_STAGE: Stage = Stage.RUNNABLE

    def process_stage(  # noqa: PLR0913
        self,
        *,
        input_path: Path,
        input_encoding: EncodingMode,
        output_encoding: EncodingMode,
        temp_file: bool = False,
        module_name: str | None = None,
    ) -> str | bytes:
        """Compile the LLVMIR artifact into a runnable program."""
        _ = input_path, input_encoding, output_encoding, temp_file, module_name

        if output_encoding == EncodingMode.TEXTUAL:
            raise UnsupportedEncodingError(self.OUTPUT_STAGE, output_encoding)

        raise NotImplementedError


class RunnerError(CompilerError):
    """Base class for Hugr compiler errors."""
