"""Console interface for guppy_runner.

The execution is composed of three steps:

    - Compile the input guppy program into a Hugr.
    - Compile the Hugr into MLIR with `hugr-mlir`, and produce an LLVMIR output file
        (either bitcode or textual).
    - Produce a runnable artifact from the LLVMIR file and the `qir-runner` runtime.
"""

import argparse
from pathlib import Path

from guppy_runner.guppy_compiler import guppy_to_hugr
from guppy_runner.hugr_compiler import MlirMode, hugr_to_mlir
from guppy_runner.mlir_compiler import compile_mlir


def arg_parser() -> argparse.ArgumentParser:
    """Returns a parser for the command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compile a Guppy program into a runnable artifact.",
    )

    # Input options

    input_args = parser.add_mutually_exclusive_group(required=True)
    input_args.add_argument(
        "-g",
        "--guppy",
        type=Path,
        metavar="GUPPY_DIR",
        help="Input Guppy program.",
    )
    input_args.add_argument(
        "--hugr",
        type=Path,
        metavar="HUGR.json",
        help="Pre-compiled Hugr json.",
    )
    input_args.add_argument(
        "--mlir",
        type=Path,
        metavar="MLIR.mlir",
        help="Pre-compiled LLVMIR (bitcode or textual) object.",
    )

    # Hugr output options

    hugr_out = parser.add_argument_group("Hugr output options")
    hugr_out.add_argument(
        "--hugr-output",
        type=Path,
        metavar="HUGR_OUTPUT.json",
        help="Hugr json output file.",
    )

    # MLIR output options

    mlir_out = parser.add_argument_group("MLIR output options")
    mlir_out.add_argument(
        "--mlir-output",
        type=Path,
        metavar="MLIR_OUTPUT.mlir",
        help="MLIR output file.",
    )
    mlir_out.add_argument(
        "--textual",
        action="store_const",
        dest="mlir_mode",
        const=MlirMode.TEXTUAL,
        default=MlirMode.BITCODE,
        help="Produce textual LLVMIR instead of bitcode.",
    )

    # Runnable artifact options

    runnable_out = parser.add_argument_group("Runnable artifact options")
    runnable_out.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="OUTPUT",
        help="Runnable artifact output file.",
    )

    return parser


def main() -> None:
    """Main entry point for the console script."""
    parser = arg_parser()
    args = parser.parse_args()

    if not args.hugr_output and not args.mlir_output and not args.output:
        parser.error(
            "No output specified. "
            "Use at least one of --hugr-output, --mlir-output, or --output.",
        )

    # Compile the input Guppy program into a Hugr.
    hugr_in: Path = args.hugr
    if args.guppy:
        hugr_in = guppy_to_hugr(args.guppy, args.hugr_output)
    elif args.hugr is not None:
        parser.error("Cannot produce a HUGR file from the given inputs.")
    if not args.mlir_output and not args.output:
        return

    # Compile the Hugr into MLIR with `hugr-mlir`, and produce an LLVMIR output file
    mlir_in: Path = args.mlir
    if hugr_in:
        mlir_in = hugr_to_mlir(hugr_in, args.mlir_output, args.mlir_mode)
    elif args.mlir is not None:
        parser.error("Cannot produce a MLIR file from the given inputs.")
    if not args.output:
        return

    # Produce a runnable artifact from the LLVMIR file and the `qir-runner` runtime.
    if mlir_in:
        compile_mlir(mlir_in, args.output)
    elif args.output is not None:
        parser.error("Cannot produce a runnable artifact from the given inputs.")


if __name__ == "__main__":
    main()
