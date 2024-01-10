"""Methods for producing runnable artifacts from MLIR objects."""

from pathlib import Path

from guppy_runner.workflow import EncodingMode, Stage, StageData, StageProcessor


def mlir_to_llvm(mlir: Path, llvm_out: Path | None) -> Path:
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
    encoding = EncodingMode.from_file(mlir, Stage.MLIR) or EncodingMode.TEXTUAL
    input_data = StageData(Stage.HUGR, mlir, encoding)
    output = MLIRCompiler().run(input_data, llvm_out=llvm_out)
    return output.file_path


class MLIRCompiler(StageProcessor):
    """A processor for compiling MLIR objects into LLVMIR."""

    INPUT_STAGE: Stage = Stage.MLIR
    OUTPUT_STAGE: Stage = Stage.LLVM

    def run(self, data: StageData, *, llvm_out: Path | None, **kwargs) -> StageData:
        """Transform the input into the following stage."""
        assert not kwargs

        if data.stage != self.INPUT_STAGE:
            err = f"Invalid input stage {data.stage}."
            raise ValueError(err)

        _ = llvm_out
        raise NotImplementedError
