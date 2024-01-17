"""Runner for the compiled guppy binary."""


import subprocess
from pathlib import Path

from guppy_runner.util import LOGGER


def run_guppy_bin(binary: Path) -> None:
    """Run the compiled guppy binary."""
    cmd = [
        binary.absolute(),
    ]

    cmd_str = " ".join(str(c) for c in cmd)
    msg = f"Executing command: '{cmd_str}'"
    LOGGER.info(msg)

    print("----------------------")
    print("Executing the program:")
    print()

    out = subprocess.run(  # noqa: PLW1510
        cmd,  # noqa: S603
        capture_output=True,
        # check=True, # This returns a non-zero code  # noqa: ERA001
        text=True,
    )

    print(out.stdout)
