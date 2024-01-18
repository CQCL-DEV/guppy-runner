"""A simple series of states for processing a Guppy program and running it."""

from __future__ import annotations

import sys
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class Stage(Enum):
    """The possible stages of a program compilation."""

    # Input guppy program.
    GUPPY = 0
    # Hugr for the program.
    HUGR = 1
    # High level MLIR
    HUGR_MLIR = 2
    # MLIR in the llvm dialect
    LOWERED_MLIR = 3
    # LLVMIR
    LLVM = 4
    # .o file
    OBJECT = 5
    # Executable file
    EXECUTABLE = 6

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

    def file_suffix(self, encoding: EncodingMode) -> str:  # noqa: PLR0911, C901
        """Returns the file suffix for the stage."""
        if self == Stage.GUPPY:
            return ".py"

        if self == Stage.HUGR and encoding == EncodingMode.BITCODE:
            return ".msgpack"
        if self == Stage.HUGR and encoding == EncodingMode.TEXTUAL:
            return ".json"

        if self == Stage.HUGR_MLIR and encoding == EncodingMode.BITCODE:
            return ".mlirbc"
        if self == Stage.HUGR_MLIR and encoding == EncodingMode.TEXTUAL:
            return ".mlir"

        if self == Stage.LOWERED_MLIR and encoding == EncodingMode.BITCODE:
            return ".mlirbc"
        if self == Stage.LOWERED_MLIR and encoding == EncodingMode.TEXTUAL:
            return ".mlir"

        if self == Stage.LLVM and encoding == EncodingMode.BITCODE:
            return ".bc"
        if self == Stage.LLVM and encoding == EncodingMode.TEXTUAL:
            return ".ll"

        if self == Stage.OBJECT:
            return ".o"

        if self == Stage.EXECUTABLE:
            return ".out"

        return ""

    def default_encoding(self) -> EncodingMode:
        """Returns the default file encoding for the stage."""
        return {
            Stage.GUPPY: EncodingMode.TEXTUAL,
            Stage.HUGR: EncodingMode.TEXTUAL,
            Stage.HUGR_MLIR: EncodingMode.TEXTUAL,
            Stage.LOWERED_MLIR: EncodingMode.TEXTUAL,
            Stage.LLVM: EncodingMode.TEXTUAL,
            Stage.OBJECT: EncodingMode.BITCODE,
            Stage.EXECUTABLE: EncodingMode.BITCODE,
        }[self]


class EncodingMode(Enum):
    """The encoding format for a compiled object.

    Either bitcode or textual.
    For Hugr objects, this corresponds to either msgpack or json.
    """

    BITCODE = 0
    TEXTUAL = 1

    @staticmethod
    def from_file(file: Path, stage: Stage) -> EncodingMode | None:  # noqa: PLR0911, C901
        """Try to derive the encoding mode from a file extension."""
        ext = file.suffix

        if stage == Stage.GUPPY:
            return EncodingMode.TEXTUAL

        if stage == Stage.HUGR and ext == ".msgpack":
            return EncodingMode.BITCODE
        if stage == Stage.HUGR and ext == ".json":
            return EncodingMode.TEXTUAL

        if stage == Stage.HUGR_MLIR and ext == ".mlirbc":
            return EncodingMode.BITCODE
        if stage == Stage.HUGR_MLIR and ext == ".mlir":
            return EncodingMode.TEXTUAL

        if stage == Stage.LOWERED_MLIR and ext == ".mlirbc":
            return EncodingMode.BITCODE
        if stage == Stage.LOWERED_MLIR and ext == ".mlir":
            return EncodingMode.TEXTUAL

        if stage == Stage.LLVM and ext == ".bc":
            return EncodingMode.BITCODE
        if stage == Stage.LLVM and ext == ".ll":
            return EncodingMode.TEXTUAL

        if stage == Stage.OBJECT:
            return EncodingMode.BITCODE

        if stage == Stage.EXECUTABLE:
            return EncodingMode.BITCODE

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
        cls,
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
        cls,
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
