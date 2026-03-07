"""Linked-program loader / validator package."""

from toolchain.link.link_manifest_io import load_link_input_doc
from toolchain.link.link_manifest_io import load_link_output_doc
from toolchain.link.link_manifest_io import save_manifest_doc
from toolchain.link.materializer import build_link_input_doc_for_program
from toolchain.link.materializer import load_linked_output_bundle
from toolchain.link.materializer import write_link_input_bundle
from toolchain.link.materializer import write_link_output_bundle
from toolchain.link.global_optimizer import LinkedProgramOptimizationResult
from toolchain.link.global_optimizer import optimize_linked_program
from toolchain.link.program_call_graph import build_linked_program_call_graph
from toolchain.link.program_call_graph import LinkedProgramCallGraph
from toolchain.link.program_loader import build_linked_program_from_module_map
from toolchain.link.program_loader import load_linked_program
from toolchain.link.program_model import LINK_INPUT_SCHEMA
from toolchain.link.program_model import LINK_OUTPUT_SCHEMA
from toolchain.link.program_model import LinkedProgram
from toolchain.link.program_model import LinkedProgramModule
from toolchain.link.program_validator import validate_link_input_doc
from toolchain.link.program_validator import validate_link_output_doc
from toolchain.link.program_validator import validate_raw_east3_doc

__all__ = [
    "LINK_INPUT_SCHEMA",
    "LINK_OUTPUT_SCHEMA",
    "LinkedProgramOptimizationResult",
    "optimize_linked_program",
    "build_linked_program_call_graph",
    "build_linked_program_from_module_map",
    "LinkedProgramCallGraph",
    "LinkedProgram",
    "LinkedProgramModule",
    "load_link_input_doc",
    "load_link_output_doc",
    "save_manifest_doc",
    "build_link_input_doc_for_program",
    "load_linked_output_bundle",
    "write_link_input_bundle",
    "write_link_output_bundle",
    "load_linked_program",
    "validate_link_input_doc",
    "validate_link_output_doc",
    "validate_raw_east3_doc",
]
