"""Go / Java / Swift / Kotlin 向け埋め込み Python トランスパイラ共通実装。"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import re
from pathlib import Path


@dataclass
class EmbeddedTranspileConfig:
    """埋め込み Python 生成設定。

    Attributes:
        language_name: 生成対象言語名（表示用）。
        file_header: 生成ファイル先頭に入れる説明コメント。
        target: 生成ターゲット（"go" / "java" / "swift" / "kotlin"）。
        runtime_template_path: 利用するランタイムテンプレートファイルパス。
    """

    language_name: str
    file_header: str
    target: str
    runtime_template_path: Path


class EmbeddedPythonTranspiler:
    """Python ソースを埋め込み実行コードへ変換する共通トランスパイラ。"""

    def __init__(self, config: EmbeddedTranspileConfig) -> None:
        """トランスパイラを初期化する。

        Args:
            config: 生成対象ごとの設定値。
        """
        self.config = config

    def transpile_path(self, input_path: Path, output_path: Path) -> str:
        """入力 Python ファイルを埋め込み実行コードへ変換する。

        Args:
            input_path: 変換元 Python ファイルパス。
            output_path: 変換先ファイルパス（Java クラス名生成に使用）。

        Returns:
            変換後コード全文。
        """
        source = input_path.read_bytes()
        encoded = base64.b64encode(source).decode("ascii")
        runtime_template = self.config.runtime_template_path.read_text(encoding="utf-8")
        if self.config.target == "go":
            return self._render_go(runtime_template, encoded)
        if self.config.target == "java":
            return self._render_java(runtime_template, encoded, output_path)
        if self.config.target == "swift":
            return self._render_swift(runtime_template, encoded, output_path)
        if self.config.target == "kotlin":
            return self._render_kotlin(runtime_template, encoded, output_path)
        raise ValueError(f"unsupported target: {self.config.target}")

    def _render_go(self, runtime_template: str, encoded: str) -> str:
        """Go 出力を組み立てる。"""
        runtime = runtime_template.rstrip()
        return (
            f"{self.config.file_header}\n\n"
            f"{runtime}\n\n"
            "// 埋め込み Python ソース（Base64）。\n"
            f"const pytraEmbeddedSourceBase64 = \"{encoded}\"\n\n"
            "// main は埋め込み Python を実行するエントリポイント。\n"
            "func main() {\n"
            "\tos.Exit(pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, os.Args[1:]))\n"
            "}\n"
        )

    def _render_java(self, runtime_template: str, encoded: str, output_path: Path) -> str:
        """Java 出力を組み立てる。"""
        runtime = runtime_template.rstrip()
        main_class_name = self._java_class_name_from_output(output_path)
        return (
            f"{self.config.file_header}\n\n"
            f"{runtime}\n\n"
            f"final class {main_class_name} {{\n"
            "    // 埋め込み Python ソース（Base64）。\n"
            f"    private static final String PYTRA_EMBEDDED_SOURCE_BASE64 = \"{encoded}\";\n\n"
            "    // main は埋め込み Python を実行するエントリポイント。\n"
            "    public static void main(String[] args) {\n"
            "        int code = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args);\n"
            "        System.exit(code);\n"
            "    }\n"
            "}\n"
        )

    def _render_swift(self, runtime_template: str, encoded: str, output_path: Path) -> str:
        """Swift 出力を組み立てる。"""
        runtime = runtime_template.rstrip()
        return (
            f"{self.config.file_header}\n\n"
            f"{runtime}\n\n"
            "// 埋め込み Python ソース（Base64）。\n"
            f"let pytraEmbeddedSourceBase64 = \"{encoded}\"\n"
            "let pytraArgs = Array(CommandLine.arguments.dropFirst())\n"
            "let pytraCode = pytraRunEmbeddedPython(pytraEmbeddedSourceBase64, pytraArgs)\n"
            "Foundation.exit(pytraCode)\n"
        )

    def _render_kotlin(self, runtime_template: str, encoded: str, output_path: Path) -> str:
        """Kotlin 出力を組み立てる。"""
        runtime = runtime_template.rstrip()
        main_class_name = self._java_class_name_from_output(output_path)
        return (
            f"{self.config.file_header}\n\n"
            f"{runtime}\n\n"
            f"class {main_class_name} {{\n"
            "    companion object {\n"
            "        // 埋め込み Python ソース（Base64）。\n"
            f"        private const val PYTRA_EMBEDDED_SOURCE_BASE64: String = \"{encoded}\"\n\n"
            "        // main は埋め込み Python を実行するエントリポイント。\n"
            "        @JvmStatic\n"
            "        fun main(args: Array<String>) {\n"
            "            val code: Int = PyRuntime.runEmbeddedPython(PYTRA_EMBEDDED_SOURCE_BASE64, args)\n"
            "            kotlin.system.exitProcess(code)\n"
            "        }\n"
            "    }\n"
            "}\n"
        )

    def _java_class_name_from_output(self, output_path: Path) -> str:
        """出力ファイル名から Java クラス名として安全な識別子を作る。"""
        stem = output_path.stem
        normalized = re.sub(r"[^0-9A-Za-z_]", "_", stem)
        if not normalized:
            normalized = "pytra_generated"
        if normalized[0].isdigit():
            normalized = f"pytra_{normalized}"
        return normalized
