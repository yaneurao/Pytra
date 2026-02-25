"""EAST -> Java transpiler.

Java 本体は Node bridge を生成し、同名 sidecar JavaScript を実行する。
"""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.emitter.js_emitter import load_js_profile


def load_java_profile() -> dict[str, Any]:
    """Java backend で利用する profile を返す。"""
    return load_js_profile()


def _java_string_literal(text: str) -> str:
    """Java 用の二重引用符文字列リテラルへエスケープする。"""
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    return '"' + out + '"'


def transpile_to_java(
    east_doc: dict[str, Any],
    js_entry_path: str = "Main.js",
    class_name: str = "Main",
) -> str:
    """EAST ドキュメントを Java ソースへ変換する。"""
    _ = east_doc
    js_path_lit = _java_string_literal(js_entry_path)
    out = ""
    out += "// このファイルは EAST -> JS bridge 用の Java 実行ラッパです。\n"
    out += "import java.util.ArrayList;\n"
    out += "import java.util.List;\n\n"
    out += "public final class " + class_name + " {\n"
    out += "    private " + class_name + "() {\n"
    out += "    }\n\n"
    out += "    public static void main(String[] args) throws Exception {\n"
    out += "        List<String> command = new ArrayList<>();\n"
    out += '        command.add("node");\n'
    out += "        command.add(" + js_path_lit + ");\n"
    out += "        for (String arg : args) {\n"
    out += "            command.add(arg);\n"
    out += "        }\n"
    out += "        Process process = new ProcessBuilder(command)\n"
    out += "            .inheritIO()\n"
    out += "            .start();\n"
    out += "        int code = process.waitFor();\n"
    out += "        if (code != 0) {\n"
    out += "            System.exit(code);\n"
    out += "        }\n"
    out += "    }\n"
    out += "}\n"
    return out
