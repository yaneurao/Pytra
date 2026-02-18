"""Swift / Kotlin 向け Node 実行ブリッジトランスパイラ。"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from pylib import re

from .js_ts_native_transpiler import JsTsConfig, JsTsNativeTranspiler


@dataclass
class SwiftKotlinNodeConfig:
    """Swift/Kotlin 生成設定。

    Attributes:
        language_name: 生成対象言語名（表示用）。
        target: 出力ターゲット（"swift" or "kotlin"）。
        file_header: 生成ファイル先頭コメント。
        runtime_template_path: 実行ランタイムテンプレート。
    """

    language_name: str
    target: str
    file_header: str
    runtime_template_path: Path


class SwiftKotlinNodeTranspiler:
    """Python ソースを Swift/Kotlin 実行用コードへ変換する。

    変換時に Python AST を JavaScript（native mode）へ変換し、
    その JavaScript コードを Base64 で埋め込んだ Swift/Kotlin を生成する。
    """

    def __init__(self, config: SwiftKotlinNodeConfig) -> None:
        """トランスパイラを初期化する。"""
        self.config = config

    def transpile_path(self, input_path: Path, output_path: Path) -> str:
        """入力 Python ファイルを Swift/Kotlin コードへ変換する。"""
        js_transpiler = JsTsNativeTranspiler(
            JsTsConfig(
                language_name="JavaScript",
                file_header="// generated internal JavaScript",
                runtime_ext="js",
            )
        )
        js_code = js_transpiler.transpile_path(input_path)
        js_base64 = base64.b64encode(js_code.encode("utf-8")).decode("ascii")
        runtime = self.config.runtime_template_path.read_text(encoding="utf-8").rstrip()

        if self.config.target == "swift":
            return self._render_swift(runtime, js_base64)
        if self.config.target == "kotlin":
            return self._render_kotlin(runtime, js_base64, output_path)
        raise ValueError(f"unsupported target: {self.config.target}")

    def _render_swift(self, runtime_template: str, js_base64: str) -> str:
        """Swift 出力を組み立てる。"""
        return (
            f"{self.config.file_header}\n\n"
            f"{runtime_template}\n\n"
            "// 埋め込み JavaScript ソース（Base64）。\n"
            f"let pytraEmbeddedJsBase64 = \"{js_base64}\"\n"
            "let pytraArgs = Array(CommandLine.arguments.dropFirst())\n"
            "let pytraCode = pytraRunEmbeddedNode(pytraEmbeddedJsBase64, pytraArgs)\n"
            "Foundation.exit(pytraCode)\n"
        )

    def _render_kotlin(self, runtime_template: str, js_base64: str, output_path: Path) -> str:
        """Kotlin 出力を組み立てる。"""
        class_name = self._kotlin_class_name_from_output(output_path)
        return (
            f"{self.config.file_header}\n\n"
            f"{runtime_template}\n\n"
            f"class {class_name} {{\n"
            "    companion object {\n"
            "        // 埋め込み JavaScript ソース（Base64）。\n"
            f"        private const val PYTRA_EMBEDDED_JS_BASE64: String = \"{js_base64}\"\n\n"
            "        // エントリポイント。\n"
            "        @JvmStatic\n"
            "        fun main(args: Array<String>) {\n"
            "            val code = PyRuntime.runEmbeddedNode(PYTRA_EMBEDDED_JS_BASE64, args)\n"
            "            kotlin.system.exitProcess(code)\n"
            "        }\n"
            "    }\n"
            "}\n"
        )

    def _kotlin_class_name_from_output(self, output_path: Path) -> str:
        """出力ファイル名から Kotlin クラス名として安全な識別子を生成する。"""
        stem = output_path.stem
        normalized = re.sub(r"[^0-9A-Za-z_]", "_", stem)
        if not normalized:
            normalized = "pytra_generated"
        if normalized[0].isdigit():
            normalized = f"pytra_{normalized}"
        return normalized
