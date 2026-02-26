"""EAST -> Go sidecar compatibility emitter.

Go 本体は Node bridge を生成し、同名 sidecar JavaScript を実行する。
native 既定経路は `go_native_emitter.py` を参照。
"""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.emitter.js_emitter import load_js_profile


def load_go_profile() -> dict[str, Any]:
    """Go backend 用 profile を返す。"""
    return load_js_profile()


def _go_string_literal(text: str) -> str:
    """Go 用の二重引用符文字列リテラルへエスケープする。"""
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    return '"' + out + '"'


def transpile_to_go(east_doc: dict[str, Any], js_entry_path: str = "program.js") -> str:
    """EAST を Go ソースへ変換する。"""
    _ = east_doc
    js_path_lit = _go_string_literal(js_entry_path)
    out = ""
    out += "// このファイルは EAST -> JS bridge 用の Go 実行ラッパです。\n"
    out += "package main\n\n"
    out += "import (\n"
    out += '    "fmt"\n'
    out += '    "os"\n'
    out += '    "os/exec"\n'
    out += ")\n\n"
    out += "func main() {\n"
    out += "    target := " + js_path_lit + "\n"
    out += "    args := []string{target}\n"
    out += "    if len(os.Args) > 1 {\n"
    out += "        args = append(args, os.Args[1:]...)\n"
    out += "    }\n"
    out += '    cmd := exec.Command("node", args...)\n'
    out += "    cmd.Stdout = os.Stdout\n"
    out += "    cmd.Stderr = os.Stderr\n"
    out += "    cmd.Stdin = os.Stdin\n"
    out += "    cmd.Env = os.Environ()\n"
    out += "    if err := cmd.Run(); err != nil {\n"
    out += "        if exitErr, ok := err.(*exec.ExitError); ok {\n"
    out += "            os.Exit(exitErr.ExitCode())\n"
    out += "        }\n"
    out += '        fmt.Fprintln(os.Stderr, "error: failed to launch node:", err)\n'
    out += "        os.Exit(1)\n"
    out += "    }\n"
    out += "}\n"
    return out
