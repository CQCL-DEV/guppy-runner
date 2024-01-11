"""Guppy Runner."""

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from guppy_runner.guppy_compiler import GuppyCompiler
from guppy_runner.hugr_compiler import HugrCompiler
from guppy_runner.mlir_compiler import MLIRCompiler
from guppy_runner.runner import Runner
from guppy_runner.util import LOGGER
from guppy_runner.workflow import (
    EncodingMode,
    ProcessorError,
    Stage,
    StageData,
    StageProcessor,
)

__all__ = [
    "run_guppy",
    "run_guppy_str",
    "run_guppy_from_stage",
]


def run_guppy(
    guppy_path: Path,
    *,
    hugr_out: Path | None = None,
    mlir_out: Path | None = None,
    llvm_out: Path | None = None,
    no_run: bool = False,
) -> bool:
    """Compile and run a Guppy program.

    :param guppy_path: The Guppy program path to run.
    :param hugr_out: Optional. If provided, write the compiled Hugr to this file.
        The file extension determines the encoding mode (json or msgpack).
    :param mlir_out: Optional. If provided, write the compiled MLIR to this file.
    :param llvm_out: Optional. If provided, write the compiled LLVMIR to this file.
    :param no_run: Optional. If True, do not run the compiled artifact.
        The compilation will terminate after producing the required intermediary files.
    :return: Whether the program ran successfully.
    """
    stage_data = StageData.from_path(
        Stage.GUPPY,
        guppy_path,
        EncodingMode.TEXTUAL,
    )

    return run_guppy_from_stage(
        stage_data,
        hugr_out=hugr_out,
        mlir_out=mlir_out,
        llvm_out=llvm_out,
        no_run=no_run,
    )


def run_guppy_str(
    guppy_program: str,
    *,
    hugr_out: Path | None = None,
    mlir_out: Path | None = None,
    llvm_out: Path | None = None,
    no_run: bool = False,
) -> bool:
    """Compile and run a Guppy program.

    :param guppy_program: The Guppy program to run.
    :param hugr_out: Optional. If provided, write the compiled Hugr to this file.
        The file extension determines the encoding mode (json or msgpack).
    :param mlir_out: Optional. If provided, write the compiled MLIR to this file.
    :param llvm_out: Optional. If provided, write the compiled LLVMIR to this file.
    :param no_run: Optional. If True, do not run the compiled artifact.
        The compilation will terminate after producing the required intermediary files.
    :return: Whether the program ran successfully.
    """
    stage_data = StageData(
        Stage.GUPPY,
        guppy_program,
        EncodingMode.TEXTUAL,
    )

    return run_guppy_from_stage(
        stage_data,
        hugr_out=hugr_out,
        mlir_out=mlir_out,
        llvm_out=llvm_out,
        no_run=no_run,
    )


def run_guppy_from_stage(
    program: StageData,
    *,
    hugr_out: Path | None = None,
    mlir_out: Path | None = None,
    llvm_out: Path | None = None,
    no_run: bool = False,
) -> bool:
    """Compile and run a Guppy program, from a given compilation stage.

    :param guppy_program: The program to run.
        If an intermediary stage is given, start compilation from that stage.
    :param hugr_out: Optional. If provided, write the compiled Hugr to this file.
        The file extension determines the encoding mode (json or msgpack).
    :param mlir_out: Optional. If provided, write the compiled MLIR to this file.
    :param llvm_out: Optional. If provided, write the compiled LLVMIR to this file.
    :param no_run: Optional. If True, do not run the compiled artifact.
        The compilation will terminate after producing the required intermediary files.
    :return: Whether the program ran successfully.
    """
    compilers = [
        GuppyCompiler(),
        HugrCompiler(),
        MLIRCompiler(),
        Runner(),
    ]

    for compiler in compilers:
        if _are_we_done(
            program.stage,
            hugr_out=hugr_out,
            mlir_out=mlir_out,
            llvm_out=llvm_out,
            no_run=no_run,
        ):
            break

        # Skip stages that are not required.
        # (e.g. if we give an intermediary artifact as input)
        if program.stage == compiler.INPUT_STAGE:
            LOGGER.info(
                "Compiling %s -> %s",
                compiler.INPUT_STAGE,
                compiler.OUTPUT_STAGE,
            )
            try:
                program = compiler.run(
                    program,
                    hugr_out=hugr_out,
                    mlir_out=mlir_out,
                    llvm_out=llvm_out,
                )
            except ProcessorError as err:
                LOGGER.error(err)
                return False

    return True


def _are_we_done(
    stage: Stage,
    *,
    hugr_out: Path | None = None,
    mlir_out: Path | None = None,
    llvm_out: Path | None = None,
    no_run: bool = False,
) -> bool:
    """Returns 'true' if we can stop the execution early."""
    if not no_run:
        return False
    if hugr_out and stage < Stage.HUGR:
        return False
    if mlir_out and stage < Stage.MLIR:
        return False
    if llvm_out and stage < Stage.LLVM:
        return False
    return True
