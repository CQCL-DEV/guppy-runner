"""Utilities to link and run the final LLVM artifact."""


from guppy_runner.workflow import StageData


def run_artifact(artifact: StageData) -> None:
    """Link the LLVM artifact and run it."""
    _ = artifact
    raise NotImplementedError


class RunnerError(Exception):
    """Base class for Hugr compiler errors."""
