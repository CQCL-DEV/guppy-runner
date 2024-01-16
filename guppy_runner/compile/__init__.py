"""A simple series of states for processing a Guppy program and running it."""

from __future__ import annotations

import sys
import tempfile
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from guppy_runner.stage import EncodingMode, Stage, StageData


class StageCompiler(ABC):
    """A compiler for a single stage of the Guppy execution workflow."""

    INPUT_STAGE: Stage
    OUTPUT_STAGE: Stage

    @abstractmethod
    def process_stage(  # noqa: PLR0913
        self,
        *,
        input_path: Path,
        input_encoding: EncodingMode,
        output_encoding: EncodingMode,
        temp_file: bool = False,
        module_name: str | None = None,
    ) -> str | bytes:
        """Execute the translation command.

        :param input_path: The input file path.
        :param input_encoding: The input encoding mode.
        :param output_encoding: The output encoding mode.
        :param temp_file: Whether the input file is a temporary file,
            instead of a user-specified file.
        :param module_name: The name of the module being compiled.
        """

    def _check_stage(self, data: StageData) -> None:
        if data.stage != self.INPUT_STAGE:
            raise InvalidStageError(data.stage, self.INPUT_STAGE)

    def _get_output_mode(
        self,
        out_file: Path | None,
        default: EncodingMode,
    ) -> EncodingMode:
        """Determine the target encoding mode from the output file extension."""
        if out_file is None:
            return default
        return EncodingMode.from_file(out_file, self.OUTPUT_STAGE) or default

    def _store_artifact(self, data: StageData, path: Path) -> None:
        mode = "w" if data.encoding == EncodingMode.TEXTUAL else "wb"
        with path.open(mode=mode) as file:
            file.write(data.data)

    def run(
        self,
        data: StageData,
        *,
        output_mode: EncodingMode | None = None,
        output_file: Path | None = None,
        module_name: str | None = None,
    ) -> StageData:
        """Transform the input into the following stage."""
        self._check_stage(data)

        # Determine the output encoding.
        if output_mode is None:
            output_mode = self._get_output_mode(
                output_file,
                default=self.OUTPUT_STAGE.default_encoding(),
            )

        if data.data_path is None:
            output_data = self._translate_data(
                data.data,
                data.encoding,
                output_mode,
                module_name=module_name,
            )
        else:
            output_data = self._translate_file(
                data.data_path,
                data.encoding,
                output_mode,
                module_name=module_name,
            )

        output = StageData(self.OUTPUT_STAGE, output_data, output_mode)

        # Write the output file if requested.
        if output_file:
            self._store_artifact(output, output_file)

        return output

    def _translate_data(
        self,
        input_data: str | bytes,
        input_encoding: EncodingMode,
        output_encoding: EncodingMode,
        module_name: str | None = None,
    ) -> str | bytes:
        """Translate data encoded in-memory.

        First writes it to a temporary file, then translates it.
        """
        mode = "w" if input_encoding == EncodingMode.TEXTUAL else "wb"
        suffix = self.INPUT_STAGE.file_suffix(input_encoding)
        with tempfile.NamedTemporaryFile(
            mode=mode,
            suffix=suffix,
            delete=False,
        ) as temp_file:
            temp_file.write(input_data)
            input_path = Path(temp_file.name)
        output = self.process_stage(
            input_path=input_path,
            input_encoding=input_encoding,
            output_encoding=output_encoding,
            temp_file=True,
            module_name=module_name,
        )
        input_path.unlink()
        return output

    def _translate_file(
        self,
        path: Path,
        input_encoding: EncodingMode,
        output_encoding: EncodingMode,
        module_name: str | None = None,
    ) -> str | bytes:
        """Translate data encoded in a file."""
        return self.process_stage(
            input_path=path,
            input_encoding=input_encoding,
            output_encoding=output_encoding,
            temp_file=False,
            module_name=module_name,
        )


class CompilerError(Exception):
    """Base class for processor errors."""


class InvalidStageError(CompilerError):
    """Invalid input data."""

    def __init__(self, stage: Stage, expected: Stage) -> None:
        """Initialize the error."""
        super().__init__(f"Expected {expected.name} artifact, got {stage.name}.")


class UnsupportedEncodingError(CompilerError):
    """Stage does not support the encoding mode."""

    def __init__(self, stage: Stage, mode: EncodingMode) -> None:
        """Initialize the error."""
        super().__init__(f"{stage.name} does not support {mode.name} encoding.")
