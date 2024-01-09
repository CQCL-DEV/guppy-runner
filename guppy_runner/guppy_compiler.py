"""Methods for compiling Guppy programs into HUGR."""


from pathlib import Path
from tempfile import TemporaryFile


def guppy_to_hugr(guppy: Path, hugr_out: Path | None) -> Path:
    """Compile the input Guppy program into a json-encoded Hugr.

    Returns the path to the json file.
    """
    hugr_out: Path = hugr_out or Path(
        TemporaryFile(mode="w", prefix="hugr_", suffix=".json"),
    )

    _ = (guppy, hugr_out)
    raise NotImplementedError
