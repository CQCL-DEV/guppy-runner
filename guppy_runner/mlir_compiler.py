"""Methods for producing runnable artifacts from MLIR objects.

We assume that the MLIR object is the result of compiling a Hugr-encoded Guppy program.
"""


from pathlib import Path


def compile_mlir(llvmir_object: Path, output: Path) -> Path:
    """Compile the input LLVMIR object into a runnable artifact.

    Returns the path to the artifact.
    """
    _ = (llvmir_object, output)
    raise NotImplementedError
