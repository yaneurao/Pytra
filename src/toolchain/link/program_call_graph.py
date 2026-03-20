"""Program-wide call graph utilities for linked programs."""

from __future__ import annotations

from dataclasses import dataclass

from toolchain.compile.east3_opt_passes.non_escape_call_graph import build_non_escape_call_graph
from toolchain.compile.east3_opt_passes.non_escape_call_graph import collect_non_escape_symbols
from toolchain.compile.east3_opt_passes.non_escape_call_graph import strongly_connected_components
from toolchain.link.program_model import LinkedProgram


@dataclass(frozen=True)
class LinkedProgramCallGraph:
    """Deterministic function-level graph extracted from a linked program."""

    graph: dict[str, tuple[str, ...]]
    unresolved_calls: dict[str, int]
    symbol_module_ids: dict[str, str]
    sccs: tuple[tuple[str, ...], ...]


def build_linked_program_call_graph(program: LinkedProgram) -> LinkedProgramCallGraph:
    known_symbols: set[str] = set()
    symbol_module_ids: dict[str, str] = {}

    for module in sorted(program.modules, key=lambda item: item.module_id):
        module_id, symbols, _local_symbol_map = collect_non_escape_symbols(module.east_doc)
        for symbol in sorted(symbols.keys()):
            known_symbols.add(symbol)
            symbol_module_ids[symbol] = module_id

    raw_graph: dict[str, set[str]] = {}
    unresolved_calls: dict[str, int] = {}
    for module in sorted(program.modules, key=lambda item: item.module_id):
        module_graph, module_unresolved = build_non_escape_call_graph(
            module.east_doc,
            known_symbols=known_symbols,
        )
        for caller in sorted(module_graph.keys()):
            raw_graph[caller] = set(sorted(module_graph[caller]))
            unresolved_calls[caller] = int(module_unresolved.get(caller, 0))

    sccs = strongly_connected_components(raw_graph)
    graph: dict[str, tuple[str, ...]] = {}
    ordered_unresolved_calls: dict[str, int] = {}
    ordered_symbol_module_ids: dict[str, str] = {}
    for caller in sorted(raw_graph.keys()):
        graph[caller] = tuple(sorted(raw_graph[caller]))
        ordered_unresolved_calls[caller] = int(unresolved_calls.get(caller, 0))
        ordered_symbol_module_ids[caller] = symbol_module_ids.get(caller, "")

    return LinkedProgramCallGraph(
        graph=graph,
        unresolved_calls=ordered_unresolved_calls,
        symbol_module_ids=ordered_symbol_module_ids,
        sccs=tuple(tuple(component) for component in sccs),
    )
