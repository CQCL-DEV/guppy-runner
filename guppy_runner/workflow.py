"""A simple series of states for processing a Guppy program and running it."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
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

    def __le__(self, other: Stage) -> bool:
        """Compare the stages."""
        return self.value <= other.value

    def __gt__(self, other: Stage) -> bool:
        """Compare the stages."""
        return self.value > other.value

    def __ge__(self, other: Stage) -> bool:
        """Compare the stages."""
        return self.value >= other.value


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

    @staticmethod
    def from_data(data: str | bytes) -> EncodingMode:
        """Try to derive the encoding mode from the type of the data."""
        if isinstance(data, str):
            return EncodingMode.TEXTUAL
        return EncodingMode.BITCODE


class StageData:
    """The data describing a compilation artifact in a given stage."""

    stage: Stage
    encoding: EncodingMode
    _data: str | bytes | None
    data_path: Path | None

    def __init__(
        self,
        stage: Stage,
        data: str | bytes,
        encoding: EncodingMode,
    ) -> None:
        """Initialize the data."""
        self.stage = stage
        self._data = data
        self.encoding = encoding
        self.data_path = None

    @classmethod
    def from_path(
        cls: StageData,
        stage: Stage,
        file_path: Path,
        encoding: EncodingMode,
    ) -> StageData:
        """Initialize the data from a file path."""
        c = cls(stage, "", encoding)
        c.data_path = file_path
        c._data = None  # noqa: SLF001
        return c

    @classmethod
    def from_stdin(
        cls: StageData,
        stage: Stage,
        encoding: EncodingMode,
    ) -> StageData:
        """Initialize the data, reading from stdin."""
        assert encoding == EncodingMode.TEXTUAL
        data = sys.stdin.read()
        return cls(stage, data, encoding)

    @property
    def data(self) -> str | bytes:
        """The data.

        If the data was specified as a path, load it.
        """
        if self._data is None:
            self.load_data()
        assert self._data is not None
        return self._data

    def load_data(self) -> None:
        """If the data is a path, load it."""
        if self._data is not None:
            # Already loaded.
            return
        if self.data_path is None:
            msg = "No data path to load."
            raise ValueError(msg)
        if self.encoding == EncodingMode.TEXTUAL:
            self._data = self.data_path.read_text()
        else:
            self._data = self.data_path.read_bytes()


class StageProcessor(ABC):
    """A processor for a single stage of a Guppy program."""

    INPUT_STAGE: Stage
    OUTPUT_STAGE: Stage

    @abstractmethod
    def run(self, data: StageData, **kwargs) -> StageData:
        """Transform the input into the following stage."""

    def _check_stage(self, data: StageData) -> None:
        if data.stage != self.INPUT_STAGE:
            raise InvalidStageError(data.stage, self.INPUT_STAGE)


class ProcessorError(Exception):
    """Base class for processor errors."""


class InvalidStageError(ProcessorError):
    """Invalid input data."""

    def __init__(self, stage: Stage, expected: Stage) -> None:
        """Initialize the error."""
        super().__init__(f"Expected {expected} artifact, got {stage}.")
