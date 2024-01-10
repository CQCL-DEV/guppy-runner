"""Utilities to link and run the final LLVM artifact."""


from guppy_runner.workflow import (
    InvalidStageError,
    ProcessorError,
    Stage,
    StageData,
    StageProcessor,
)


def run_artifact(artifact: StageData) -> None:
    """Link the LLVM artifact and run it."""
    _ = artifact
    if artifact.stage != Stage.LLVM:
        raise InvalidStageError(artifact.stage, Stage.LLVM)

    raise NotImplementedError


class Runner(StageProcessor):
    """A processor for running an LLVMIR artifact."""

    INPUT_STAGE: Stage = Stage.LLVM
    OUTPUT_STAGE: Stage = Stage.LLVM

    def run(self, data: StageData, **kwargs) -> StageData:
        """Run the LLVMIR artifact."""
        assert not kwargs
        self._check_stage(data)

        raise NotImplementedError


class RunnerError(ProcessorError):
    """Base class for Hugr compiler errors."""
