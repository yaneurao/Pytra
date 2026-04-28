"""EAST3 -> Julia source emitter."""

from __future__ import annotations

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.emit.common.code_emitter import RuntimeMapping
from toolchain.emit.common.code_emitter import load_runtime_mapping
from toolchain.emit.common.code_emitter import should_skip_module
from toolchain.emit.common.common_renderer import CommonRenderer
from toolchain.emit.julia.bootstrap import JuliaBootstrapRewriter
from toolchain.emit.julia.bootstrap import JuliaLegacyEmitterBridge
from toolchain.emit.julia.bootstrap import module_id_from_doc
from toolchain.emit.julia.bootstrap import prepare_module_for_emit
from toolchain.emit.julia.subset import JuliaSubsetRenderer
from toolchain.emit.julia.subset import can_render_module_natively

class JuliaRenderer(CommonRenderer):
    """Bootstrap renderer for Julia.

    The renderer already owns the toolchain2 profile and runtime mapping so the
    future port can replace legacy delegation incrementally without changing the
    public entrypoint.
    """

    mapping: RuntimeMapping
    def __init__(self) -> None:
        super().__init__("julia")
        mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "julia" / "mapping.json"
        self.mapping = load_runtime_mapping(mapping_path)

    def _module_id_from_doc(self, east3_doc: dict[str, JsonVal]) -> str:
        return module_id_from_doc(east3_doc)

    def _prepare_module_for_emit(self, east3_doc: dict[str, JsonVal]) -> tuple[str, dict[str, JsonVal]]:
        return prepare_module_for_emit(east3_doc)

    def _rewrite_legacy_compatible_doc(self, east3_doc: dict[str, JsonVal]) -> dict[str, JsonVal]:
        rewriter = JuliaBootstrapRewriter()
        return rewriter.rewrite_document(east3_doc)

    def _render_native_module(self, east3_doc: dict[str, JsonVal]) -> str:
        meta = east3_doc.get("meta")
        subset_meta = meta if isinstance(meta, dict) else {}
        return JuliaSubsetRenderer(self.mapping, subset_meta).render_module(east3_doc)

    def _render_legacy_module(self, east3_doc: dict[str, JsonVal]) -> str:
        legacy_bridge = JuliaLegacyEmitterBridge(self.mapping)
        return legacy_bridge.emit_module(east3_doc)

    def emit_module(self, east3_doc: dict[str, JsonVal]) -> str:
        return self.render_module(east3_doc)

    def render_module(self, east3_doc: dict[str, JsonVal]) -> str:
        module_id, prepared = self._prepare_module_for_emit(east3_doc)
        if should_skip_module(module_id, self.mapping):
            return ""
        rewritten_doc = self._rewrite_legacy_compatible_doc(prepared)
        if can_render_module_natively(rewritten_doc):
            try:
                return self._render_native_module(rewritten_doc)
            except RuntimeError:
                return self._render_legacy_module(rewritten_doc)
        return self._render_legacy_module(rewritten_doc)


def emit_julia_module(east3_doc: dict[str, JsonVal]) -> str:
    """Emit a Julia module from an EAST3 document."""
    renderer = JuliaRenderer()
    return renderer.emit_module(east3_doc)


def transpile_to_julia(east3_doc: dict[str, JsonVal]) -> str:
    """Public toolchain2 API: EAST3 -> Julia source."""
    return emit_julia_module(east3_doc)


def transpile_to_julia_native(east3_doc: dict[str, JsonVal]) -> str:
    """Compatibility alias used by tests and legacy entrypoints."""
    return emit_julia_module(east3_doc)
