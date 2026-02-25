"""EAST -> Swift transpiler.

Swift 本体は Node bridge を生成し、同名 sidecar JavaScript を実行する。
"""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.emitter.js_emitter import load_js_profile


def load_swift_profile() -> dict[str, Any]:
    """Swift backend で利用する profile を返す。"""
    return load_js_profile()


def _swift_string_literal(text: str) -> str:
    """Swift 用の二重引用符文字列リテラルへエスケープする。"""
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    return '"' + out + '"'


def transpile_to_swift(east_doc: dict[str, Any], js_entry_path: str = "program.js") -> str:
    """EAST を Swift ソースへ変換する。"""
    _ = east_doc
    js_path_lit = _swift_string_literal(js_entry_path)
    out = ""
    out += "// このファイルは EAST -> JS bridge 用の Swift 実行ラッパです。\n"
    out += "// PYTRA_JS_ENTRY: " + js_entry_path + "\n"
    out += "import Foundation\n"
    out += "import Glibc\n\n"
    out += "@main\n"
    out += "struct Main {\n"
    out += "    static func main() {\n"
    out += "        let process = Process()\n"
    out += '        process.executableURL = URL(fileURLWithPath: "/usr/bin/env")\n'
    out += "        var args: [String] = [\"node\", " + js_path_lit + "]\n"
    out += "        args.append(contentsOf: CommandLine.arguments.dropFirst())\n"
    out += "        process.arguments = args\n"
    out += "        process.standardInput = FileHandle.standardInput\n"
    out += "        process.standardOutput = FileHandle.standardOutput\n"
    out += "        process.standardError = FileHandle.standardError\n"
    out += "        do {\n"
    out += "            try process.run()\n"
    out += "            process.waitUntilExit()\n"
    out += "        } catch {\n"
    out += "            fputs(\"error: failed to launch node\\n\", stderr)\n"
    out += "            exit(1)\n"
    out += "        }\n"
    out += "        if process.terminationStatus != 0 {\n"
    out += "            exit(process.terminationStatus)\n"
    out += "        }\n"
    out += "    }\n"
    out += "}\n"
    return out
