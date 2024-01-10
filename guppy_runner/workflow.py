"""A simple series of states for processing a Guppy program and running it."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class Stage(Enum):
    """The possible stages of a program compilation."""

    GUPPY = 0
    HUGR = 1
    MLIR = 2
    LLVM = 3
    RUNNABLE = 4

    def __lt__(self, other: Stage) -> bool:
        """Compare the stages."""
        return self.value < other.value


class EncodingMode(Enum):
    """The encoding format for a compiled object.

    Either bitcode or textual.
    For Hugr objects, this corresponds to either msgpack or json.
    """

    BITCODE = 0
    TEXTUAL = 1

    @staticmethod
    def from_file(file: Path, stage: Stage) -> EncodingMode | None:
        """Try to derive the encoding mode from a file extension."""
        ext = file.suffix
        if stage == Stage.HUGR and ext == ".msgpack":
            return EncodingMode.BITCODE
        if stage == Stage.HUGR and ext == ".json":
            return EncodingMode.TEXTUAL
        if stage == Stage.MLIR and ext == ".mlir":
            return EncodingMode.TEXTUAL
        return None


@dataclass(frozen=True)
class StageData:
    """The data describing a compilation artifact in a given stage."""

    stage: Stage
    file_path: Path
    encoding: EncodingMode


class StageProcessor(ABC):
    """A processor for a single stage of a Guppy program."""

    INPUT_STAGE: Stage
    OUTPUT_STAGE: Stage

    @abstractmethod
    def run(self, data: StageData, **kwargs) -> StageData:
        """Transform the input into the following stage."""
