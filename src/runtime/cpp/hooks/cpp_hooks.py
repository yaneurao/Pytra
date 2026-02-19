"""C++ 向け CodeEmitter hooks 実装。"""

from __future__ import annotations

from pylib.std.typing import Any


class CppHooks:
    """C++ エミッタの拡張フック定義。

    既定では全て None を返し、標準の出力経路を維持する。
    profile で表現しにくい例外ケースのみをここへ寄せる。
    """

    def on_emit_stmt(self, emitter: Any, stmt: dict[str, Any]) -> bool | None:
        """文出力前フック。True を返すと既定処理をスキップする。"""
        return None

    def _render_save_gif(self, args: list[str], kw: dict[str, str]) -> str:
        """`save_gif` 呼び出しを C++ ランタイムシグネチャへ整形する。"""
        path = args[0] if len(args) >= 1 else '""'
        w = args[1] if len(args) >= 2 else "0"
        h = args[2] if len(args) >= 3 else "0"
        frames = args[3] if len(args) >= 4 else "list<bytearray>{}"
        palette = args[4] if len(args) >= 5 else "grayscale_palette()"
        if palette in {"nullptr", "std::nullopt"}:
            palette = "grayscale_palette()"
        delay_cs = kw.get("delay_cs", args[5] if len(args) >= 6 else "4")
        loop = kw.get("loop", args[6] if len(args) >= 7 else "0")
        return f"save_gif({path}, {w}, {h}, {frames}, {palette}, {delay_cs}, {loop})"

    def on_render_call(
        self,
        emitter: Any,
        call_node: dict[str, Any],
        func_node: dict[str, Any],
        rendered_args: list[str],
        rendered_kwargs: dict[str, str],
    ) -> str | None:
        """Call 式出力フック。文字列を返すとその式を採用する。"""
        fn_kind = emitter.any_dict_get_str(func_node, "kind", "")
        if fn_kind == "Name":
            fn_name = emitter.any_dict_get_str(func_node, "id", "")
            sym = emitter._resolve_imported_symbol(fn_name)
            module_name = emitter.any_dict_get_str(sym, "module", "")
            symbol_name = emitter.any_dict_get_str(sym, "name", "")
            if module_name in {"pylib", "pylib.tra"} and symbol_name == "png":
                return f"png_helper::write_rgb_png({', '.join(rendered_args)})"
            if module_name in {"pylib", "pylib.tra"} and symbol_name == "gif":
                return self._render_save_gif(rendered_args, rendered_kwargs)

        if fn_kind == "Attribute":
            owner_node = emitter.any_to_dict_or_empty(func_node.get("value"))
            owner_expr = emitter.render_expr(func_node.get("value"))
            owner_mod = emitter._resolve_imported_module_name(owner_expr)
            attr = emitter.any_dict_get_str(func_node, "attr", "")
            if owner_node.get("kind") in {"Name", "Attribute"}:
                if owner_mod in {"png_helper", "png", "pylib.tra.png"} and attr == "write_rgb_png":
                    return f"png_helper::write_rgb_png({', '.join(rendered_args)})"
                if owner_mod in {"gif_helper", "gif", "pylib.tra.gif"} and attr == "save_gif":
                    return self._render_save_gif(rendered_args, rendered_kwargs)
        return None

    def on_render_binop(
        self,
        emitter: Any,
        binop_node: dict[str, Any],
        left: str,
        right: str,
    ) -> str | None:
        """BinOp 出力フック。文字列を返すとその式を採用する。"""
        return None
