"""Methods for compiling HUGR-encoded guppy programs into MLIR objects."""


from pathlib import Path

from guppy_runner.workflow import EncodingMode, Stage, StageData, StageProcessor


def hugr_to_mlir(hugr: Path, mlir_out: Path | None) -> Path:
    """Compile the input Hugr into an MLIR object.

    ## Parameters
    hugr: Path
        The path to the input Hugr msgpack or json encoded file.
        The file extension determines the encoding mode.
    mlir_out: Path | None
        The path to the output file.

    ## Returns
    Returns the path to the output file.
    """
    encoding = EncodingMode.from_file(hugr, Stage.HUGR) or EncodingMode.TEXTUAL
    input_data = StageData(Stage.HUGR, hugr, encoding)
    output = HugrCompiler().run(input_data, mlir_out=mlir_out)
    return output.file_path


class HugrCompiler(StageProcessor):
    """A processor for compiling Hugr objects into MLIR."""

    INPUT_STAGE: Stage = Stage.HUGR
    OUTPUT_STAGE: Stage = Stage.MLIR

    def run(self, data: StageData, *, mlir_out: Path | None, **kwargs) -> StageData:
        """Transform the input into the following stage."""
        assert not kwargs

        if data.stage != self.INPUT_STAGE:
            err = f"Invalid input stage {data.stage}."
            raise ValueError(err)

        _ = mlir_out
        raise NotImplementedError
