"""Console interface for guppy_runner.

The execution is composed of three steps:

    - Compile the input guppy program into a Hugr.
    - Compile the Hugr into MLIR with `hugr-mlir`, and produce an LLVMIR output file
        (either bitcode or textual).
    - Produce a runnable artifact from the LLVMIR file and the `qir-runner` runtime.
"""

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from guppy_runner.guppy_compiler import GuppyCompilerError, guppy_to_hugr
from guppy_runner.hugr_compiler import MlirMode, hugr_to_mlir
from guppy_runner.mlir_compiler import compile_mlir


def arg_parser() -> ArgumentParser:
    """Returns a parser for the command line arguments."""
    parser = ArgumentParser(
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
        metavar="HUGR.msgpack",
        help="Pre-compiled Hugr msgpack.",
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
        metavar="HUGR_OUTPUT.msgpack",
        help="Hugr msgpack output file.",
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
    hugr_in = run_guppy_to_hugr(args, parser)
    if not args.mlir_output and not args.output:
        return

    # Compile the Hugr into MLIR with `hugr-mlir`, and produce an LLVMIR output file
    mlir_in = run_hugr_to_mlir(hugr_in, args, parser)
    if not args.output:
        return

    # Produce a runnable artifact from the LLVMIR file and the `qir-runner` runtime.
    run_mlir_to_artifact(mlir_in, args, parser)


def run_guppy_to_hugr(args: Namespace, parser: ArgumentParser) -> Path | None:
    """Compile the input Guppy program into a Hugr, if needed.

    Returns the path to the compiled Hugr file.
    """
    hugr_in: Path = args.hugr
    if args.guppy:
        try:
            hugr_in = guppy_to_hugr(args.guppy, args.hugr_output)
        except GuppyCompilerError as err:
            exit_with_error(str(err))
    elif args.hugr is not None:
        parser.error("Cannot produce a HUGR file from the given inputs.")

    return hugr_in


def run_hugr_to_mlir(
    hugr_in: Path | None,
    args: Namespace,
    parser: ArgumentParser,
) -> Path | None:
    """Compile the input Hugr into a MLIR, if needed.

    Returns the path to the compiled MLIR file.
    """
    mlir_in: Path = args.mlir
    if hugr_in:
        try:
            mlir_in = hugr_to_mlir(hugr_in, args.mlir_output, args.mlir_mode)
        except Exception as err:  # noqa: BLE001
            exit_with_error(str(err))
    elif args.mlir is not None:
        parser.error("Cannot produce a MLIR file from the given inputs.")

    return mlir_in


def run_mlir_to_artifact(
    mlir_in: Path | None,
    args: Namespace,
    parser: ArgumentParser,
) -> None:
    """Compile the input MLIR into a runnable artifact."""
    if mlir_in:
        try:
            compile_mlir(mlir_in, args.output)
        except Exception as err:  # noqa: BLE001
            exit_with_error(str(err))
    elif args.output is not None:
        parser.error("Cannot produce a runnable artifact from the given inputs.")


def exit_with_error(msg: str) -> None:
    """Print an error message and exit with an error code."""
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
