"""Guppy Runner."""

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from guppylang.module import GuppyModule  # type: ignore

from guppy_runner.compile import CompilerError
from guppy_runner.compile.guppy_compiler import GuppyCompiler
from guppy_runner.compile.hugr_compiler import HugrCompiler
from guppy_runner.compile.linker import Linker
from guppy_runner.compile.llvm_compiler import LlvmCompiler
from guppy_runner.compile.mlir_compiler import MLIRCompiler
from guppy_runner.compile.mlir_lowerer import MLIRLowerer
from guppy_runner.run import run_guppy_bin
from guppy_runner.stage import EncodingMode, Stage, StageData
from guppy_runner.util import LOGGER

__all__ = [
    "run_guppy",
    "run_guppy_str",
    "run_guppy_from_stage",
]


def run_guppy(  # noqa: PLR0913
    guppy_path: Path,
    *,
    hugr_out: Path | None = None,
    hugr_mlir_out: Path | None = None,
    lowered_mlir_out: Path | None = None,
    llvm_out: Path | None = None,
    obj_out: Path | None = None,
    bin_out: Path | None = None,
    no_run: bool = False,
    module_name: str | None = None,
) -> bool:
    """Compile and run a Guppy program.

    :param guppy_path: The Guppy program path to run.
    :param hugr_out: Optional. If provided, write the compiled Hugr to this file.
        The file extension determines the encoding mode (json or msgpack).
    :param hugr_mlir_out: Optional. If provided, write the hugr-dialect MLIR to this
        file.
    :param lowered_mlir_out: Optional. If provided, write the llvm-dialect MLIR to this
        file.
    :param llvm_out: Optional. If provided, write the compiled LLVMIR to this file.
    :param no_run: Optional. If True, do not run the compiled artifact.
        The compilation will terminate after producing the required intermediary files.
    :param module_name: Optional. The name of the module to load. By default,
        compiles the module used by @guppy.
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
        hugr_mlir_out=hugr_mlir_out,
        lowered_mlir_out=lowered_mlir_out,
        llvm_out=llvm_out,
        obj_out=obj_out,
        bin_out=bin_out,
        no_run=no_run,
        module_name=module_name,
    )


def run_guppy_str(  # noqa: PLR0913
    guppy_program: str,
    *,
    hugr_out: Path | None = None,
    hugr_mlir_out: Path | None = None,
    lowered_mlir_out: Path | None = None,
    llvm_out: Path | None = None,
    obj_out: Path | None = None,
    bin_out: Path | None = None,
    no_run: bool = False,
    module_name: str | None = None,
) -> bool:
    """Compile and run a Guppy program.

    :param guppy_program: The Guppy program to run.
    :param hugr_out: Optional. If provided, write the compiled Hugr to this file.
        The file extension determines the encoding mode (json or msgpack).
    :param hugr_mlir_out: Optional. If provided, write the hugr-dialect MLIR to this
        file.
    :param lowered_mlir_out: Optional. If provided, write the llvm-dialect MLIR to this
        file.
    :param llvm_out: Optional. If provided, write the compiled LLVMIR to this file.
    :param obj_out: Optional. If provided, write the compiled object to this
        file.
    :param bin_out: Optional. If provided, write the compiled binary to this
        file.
    :param no_run: Optional. If True, do not run the compiled artifact.
        The compilation will terminate after producing the required intermediary files.
    :param module_name: Optional. The name of the module to load. By default,
        compiles the module used by @guppy.
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
        hugr_mlir_out=hugr_mlir_out,
        lowered_mlir_out=lowered_mlir_out,
        llvm_out=llvm_out,
        obj_out=obj_out,
        bin_out=bin_out,
        no_run=no_run,
        module_name=module_name,
    )


def run_guppy_module(  # noqa: PLR0913
    module: GuppyModule,
    *,
    hugr_out: Path | None = None,
    hugr_mlir_out: Path | None = None,
    lowered_mlir_out: Path | None = None,
    llvm_out: Path | None = None,
    obj_out: Path | None = None,
    bin_out: Path | None = None,
    no_run: bool = False,
    module_name: str | None = None,
) -> bool:
    """Compile and run a Guppy program.

    :param guppy_program: The Guppy program to run.
    :param hugr_out: Optional. If provided, write the compiled Hugr to this file.
        The file extension determines the encoding mode (json or msgpack).
    :param hugr_mlir_out: Optional. If provided, write the hugr-dialect MLIR to this
        file.
    :param lowered_mlir_out: Optional. If provided, write the llvm-dialect MLIR to this
        file.
    :param llvm_out: Optional. If provided, write the compiled LLVMIR to this file.
    :param obj_out: Optional. If provided, write the compiled object to this
        file.
    :param bin_out: Optional. If provided, write the compiled binary to this
        file.
    :param no_run: Optional. If True, do not run the compiled artifact.
        The compilation will terminate after producing the required intermediary files.
    :param module_name: Optional. The name of the module to load. By default,
        compiles the module used by @guppy.
    :return: Whether the program ran successfully.
    """
    hugr = module.compile()
    serial_hugr = hugr.serialize()

    stage_data = StageData(
        Stage.HUGR,
        serial_hugr,
        EncodingMode.BITCODE,
    )

    return run_guppy_from_stage(
        stage_data,
        hugr_out=hugr_out,
        hugr_mlir_out=hugr_mlir_out,
        lowered_mlir_out=lowered_mlir_out,
        llvm_out=llvm_out,
        obj_out=obj_out,
        bin_out=bin_out,
        no_run=no_run,
        module_name=module_name,
    )


def run_guppy_from_stage(  # noqa: PLR0913
    program: StageData,
    *,
    hugr_out: Path | None = None,
    hugr_mlir_out: Path | None = None,
    lowered_mlir_out: Path | None = None,
    llvm_out: Path | None = None,
    obj_out: Path | None = None,
    bin_out: Path | None = None,
    no_run: bool = False,
    module_name: str | None = None,
) -> bool:
    """Compile and run a Guppy program, from a given compilation stage.

    :param guppy_program: The program to run. If an intermediary stage is given,
        start compilation from that stage.
    :param hugr_out: Optional. If provided, write the compiled Hugr to this
        file. The file extension determines the encoding mode (json or msgpack).
    :param hugr_mlir_out: Optional. If provided, write the hugr-dialect MLIR to this
        file.
    :param lowered_mlir_out: Optional. If provided, write the llvm-dialect MLIR to this
        file.
    :param llvm_out: Optional. If provided, write the compiled LLVMIR to this
        file.
    :param obj_out: Optional. If provided, write the compiled object to this
        file.
    :param bin_out: Optional. If provided, write the compiled binary to this
        file.
    :param no_run: Optional. If True, do not run the compiled artifact. The
        compilation will terminate after producing the required intermediary
        files.
    :param module_name: Optional. The name of the module to load. By default,
        compiles the module used by @guppy.
    :return: Whether the program ran successfully.
    """
    compilers = [
        GuppyCompiler(),
        HugrCompiler(),
        MLIRLowerer(),
        MLIRCompiler(),
        LlvmCompiler(),
        Linker(),
    ]
    output_files = [
        hugr_out,
        hugr_mlir_out,
        lowered_mlir_out,
        llvm_out,
        obj_out,
        bin_out,
    ]

    for compiler, output_file in zip(compilers, output_files, strict=True):
        if _are_we_done(
            program.stage,
            hugr_out=hugr_out,
            hugr_mlir_out=hugr_mlir_out,
            lowered_mlir_out=lowered_mlir_out,
            llvm_out=llvm_out,
            obj_out=obj_out,
            bin_out=bin_out,
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
                    output_file=output_file,
                    module_name=module_name,
                )
            except CompilerError as err:
                LOGGER.error(err)
                return False

    if not no_run:
        assert program.stage == Stage.EXECUTABLE
        assert program.data_path

        run_guppy_bin(program.data_path)

    return True


def _are_we_done(  # noqa: PLR0913, PLR0911
    stage: Stage,
    *,
    hugr_out: Path | None = None,
    hugr_mlir_out: Path | None = None,
    lowered_mlir_out: Path | None = None,
    llvm_out: Path | None = None,
    obj_out: Path | None = None,
    bin_out: Path | None = None,
    no_run: bool = False,
) -> bool:
    """Returns 'true' if we can stop the execution early."""
    if not no_run:
        return False
    if hugr_out and stage < Stage.HUGR:
        return False
    if hugr_mlir_out and stage < Stage.HUGR_MLIR:
        return False
    if lowered_mlir_out and stage < Stage.LOWERED_MLIR:
        return False
    if llvm_out and stage < Stage.LLVM:
        return False
    if obj_out and stage < Stage.OBJECT:
        return False
    if bin_out and stage < Stage.EXECUTABLE:
        return False
    return True
