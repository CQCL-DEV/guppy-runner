"""Runner for the compiled guppy binary."""


import subprocess
from pathlib import Path

from guppy_runner.util import LOGGER


def run_guppy_bin(binary: Path) -> None:
    """Run the compiled guppy binary."""
    cmd = [
        binary,
    ]

    cmd_str = " ".join(str(c) for c in cmd)
    msg = f"Executing command: '{cmd_str}'"
    LOGGER.info(msg)

    subprocess.run(
        cmd,  # noqa: S603
        capture_output=True,
        check=True,
        text=False,
    )
