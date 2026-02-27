"""EAST -> Kotlin sidecar compatibility emitter.

Kotlin 本体は Node bridge を生成し、同名 sidecar JavaScript を実行する。
native 既定経路は `kotlin_native_emitter.py` を参照。
"""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.emitter.js_emitter import load_js_profile


def load_kotlin_profile() -> dict[str, Any]:
    """Kotlin backend で利用する profile を返す。"""
    return load_js_profile()


def _kotlin_string_literal(text: str) -> str:
    """Kotlin 用の二重引用符文字列リテラルへエスケープする。"""
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    return '"' + out + '"'


def transpile_to_kotlin(east_doc: dict[str, Any], js_entry_path: str = "program.js") -> str:
    """EAST を Kotlin ソースへ変換する。"""
    _ = east_doc
    js_path_lit = _kotlin_string_literal(js_entry_path)
    out = ""
    out += "// このファイルは EAST -> JS bridge 用の Kotlin 実行ラッパです。\n"
    out += "import kotlin.system.exitProcess\n\n"
    out += "fun main(args: Array<String>) {\n"
    out += "    val command = mutableListOf<String>()\n"
    out += '    command.add("node")\n'
    out += "    command.add(" + js_path_lit + ")\n"
    out += "    command.addAll(args)\n"
    out += "    val process = ProcessBuilder(command)\n"
    out += "        .inheritIO()\n"
    out += "        .start()\n"
    out += "    val code = process.waitFor()\n"
    out += "    if (code != 0) {\n"
    out += "        exitProcess(code)\n"
    out += "    }\n"
    out += "}\n"
    return out
