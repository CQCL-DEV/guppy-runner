"""Console interface for guppy_runner.

The execution is composed of three steps:

    - Compile the input guppy program into a Hugr.
    - Compile the Hugr into MLIR with `hugr-mlir`, and produce an LLVMIR output file
        (either bitcode or textual).
    - Produce a runnable artifact from the LLVMIR file and the `qir-runner` runtime.
"""

import logging
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from guppy_runner.guppy_compiler import GuppyCompiler, GuppyCompilerError
from guppy_runner.hugr_compiler import HugrCompiler, HugrCompilerError
from guppy_runner.mlir_compiler import MLIRCompiler, MLIRCompilerError
from guppy_runner.runner import RunnerError, run_artifact
from guppy_runner.workflow import EncodingMode, Stage, StageData

LOGGER = logging.getLogger(__name__)


def parse_args() -> Namespace:
    """Returns a parser for the command line arguments."""
    parser = ArgumentParser(
        description="Compile a Guppy program into a runnable artifact.",
    )

    # Input options

    input_args = parser.add_argument_group("Input options")
    input_args.add_argument(
        "-i",
        "--input",
        type=Path,
        metavar="INPUT",
        help="Input program.\n"
        "By default, this expects a Guppy program (.py)"
        "which defines a `main` GuppyModule."
        "If not given, the input is read from stdin.",
    )
    input_mode = input_args.add_mutually_exclusive_group()
    input_mode.add_argument(
        "--hugr",
        action="store_true",
        help="Read the input as an encoded Hugr.\n"
        "The input file extension determines whether the file is encoded in msgpack or "
        "json. Use `--bitcode` to `--textual` to override this.",
    )
    input_mode.add_argument(
        "--mlir",
        action="store_true",
        help="Read the input as an mlir file.",
    )
    input_mode.add_argument(
        "--llvm",
        action="store_true",
        help="Read the input as an LLVMIR file.",
    )

    input_encoding = input_args.add_mutually_exclusive_group()
    input_encoding.add_argument(
        "--bitcode",
        action="store_true",
        help="Parse the input in binary mode. "
        "By default, the encoding mode is detected from the file extension "
        "if possible.",
    )
    input_encoding.add_argument(
        "--textual",
        action="store_true",
        help="Parse the input in human-readable textual mode. "
        "By default, the encoding mode is detected from the file extension "
        "if possible.",
    )

    # Intermediary output options

    artifacts = parser.add_argument_group("Intermediary artifact outputs.")
    artifacts.add_argument(
        "--store-hugr",
        type=Path,
        metavar="HUGR_OUTPUT[.msgpack|.json]",
        help="Store the intermediary Hugr object. "
        "The file extension determines whether the file is encoded in msgpack or json.",
    )
    artifacts.add_argument(
        "--store-mlir",
        type=Path,
        metavar="MLIR.mlir",
        help="Store the intermediary MLIR object, in textual mode.",
        # TODO: Support bitcode too.  # noqa: TD002, TD003, FIX002
        # Can we detect the encoding mode from the file extension?
    )
    artifacts.add_argument(
        "--store-llvm",
        type=Path,
        metavar="LLVM.llvmir",
        help="Store the intermediary LLVMIR object, in textual mode.",
        # TODO: Support bitcode too.  # noqa: TD002, TD003, FIX002
        # Can we detect the encoding mode from the file extension?
    )

    # Runnable artifact options

    runnable = parser.add_argument_group("Runnable artifact options")
    runnable.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="OUTPUT",
        help="Runnable artifact output file.",
    )
    runnable.add_argument(
        "--no-run",
        action="store_true",
        help="Do not run the compiled artifact. "
        "`guppy-runner` will produce any required intermediary files, "
        "and terminate early.",
    )

    args = parser.parse_args()
    args.input_stage = get_input_state(args)
    args.input_encoding = get_input_encoding(args)
    validate_args(args, parser)

    return args


def get_input_state(args: Namespace) -> Stage:
    """The stage of the input file."""
    if args.hugr:
        return Stage.HUGR
    if args.mlir:
        return Stage.MLIR
    if args.llvm:
        return Stage.LLVM
    return Stage.GUPPY


def get_input_encoding(args: Namespace) -> EncodingMode:
    """The stage of the input file.

    If the encoding mode is not given, try to detect it from the file extension.
    """
    if args.textual:
        return EncodingMode.TEXTUAL
    if args.bitcode:
        return EncodingMode.BITCODE

    input_encoding = None
    if args.input is not None:
        input_encoding = EncodingMode.from_file(args.input, args.input_stage)
    if input_encoding is None:
        LOGGER.info(
            "Cannot detect the encoding mode from the input file extension. "
            "Defaulting to bitcode.",
        )
        input_encoding = EncodingMode.BITCODE
    return input_encoding


def validate_args(args: Namespace, parser: ArgumentParser) -> None:
    """Validate whether can produce the intermediary artifacts from the input."""
    if args.store_hugr and args.input_stage >= Stage.HUGR:
        parser.error("Cannot produce a HUGR artifact from the given input.")
    if args.store_mlir and args.input_stage >= Stage.MLIR:
        parser.error("Cannot produce a MLIR artifact from the given input.")
    if args.store_llvm and args.input_stage >= Stage.LLVM:
        parser.error("Cannot produce a LLVM artifact from the given input.")


def main() -> None:
    """Main entry point for the console script."""
    args = parse_args()

    stage_data = StageData(
        stage=args.input_stage,
        file_path=args.input,
        encoding=args.input_encoding,
    )

    # Process the program, stage by stage.
    if stage_data.stage == Stage.GUPPY:
        try:
            stage_data = GuppyCompiler().run(stage_data, hugr_out=args.store_hugr)
        except GuppyCompilerError as err:
            exit_with_error(str(err))
    exit_if_done(stage_data.stage, args)

    if stage_data.stage == Stage.HUGR:
        try:
            stage_data = HugrCompiler().run(stage_data, mlir_out=args.store_mlir)
        except HugrCompilerError as err:  # noqa: BLE001
            exit_with_error(str(err))
    exit_if_done(stage_data.stage, args)

    if stage_data.stage == Stage.MLIR:
        try:
            stage_data = MLIRCompiler().run(stage_data, llvm_out=args.store_llvm)
        except MLIRCompilerError as err:  # noqa: BLE001
            exit_with_error(str(err))
    exit_if_done(stage_data.stage, args)

    assert stage_data.stage == Stage.LLVM
    try:
        run_artifact(stage_data)
    except RunnerError as err:  # noqa: BLE001
        exit_with_error(str(err))
    exit_if_done(stage_data.stage, args)


def exit_with_error(msg: str) -> None:
    """Print an error message and exit with an error code."""
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def exit_if_done(stage: Stage, args: Namespace) -> None:
    """Exit if `--no-run` is set, and we already produced all the required artifacts."""
    if not args.no_run:
        return
    if args.store_llvm and stage < Stage.LLVM:
        return
    if args.store_mlir and stage < Stage.MLIR:
        return
    if args.store_hugr and stage < Stage.HUGR:
        return

    sys.exit(0)


if __name__ == "__main__":
    main()
