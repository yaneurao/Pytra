"""Node.js 向け埋め込み Python トランスパイラ共通実装。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class NodeEmbeddedTranspileConfig:
    """Node 向け生成設定。

    Attributes:
        language_name: 生成対象言語名（表示用）。
        file_header: 生成ファイル先頭に入れる説明コメント。
        use_typescript: TypeScript 構文を使うかどうか。
    """

    language_name: str
    file_header: str
    use_typescript: bool


class NodeEmbeddedPythonTranspiler:
    """Python ソースを Node 実行用コードへ変換する共通トランスパイラ。"""

    def __init__(self, config: NodeEmbeddedTranspileConfig) -> None:
        """トランスパイラを初期化する。

        Args:
            config: 生成対象ごとの設定値。
        """
        self.config = config

    def transpile_path(self, input_path: Path) -> str:
        """入力 Python ファイルを Node 実行コードへ変換する。

        Args:
            input_path: 変換元 Python ファイルパス。

        Returns:
            変換後コード全文。
        """
        source = input_path.read_text(encoding="utf-8")
        source_literal = self._js_string_literal(source)
        display_path = str(input_path).replace("\\", "/")
        if self.config.use_typescript:
            return self._render_typescript(source_literal, display_path)
        return self._render_javascript(source_literal, display_path)

    def _js_string_literal(self, value: str) -> str:
        """JavaScript/TypeScript 用の安全な文字列リテラルへ変換する。"""
        escaped = value.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        return f"`{escaped}`"

    def _render_javascript(self, source_literal: str, display_path: str) -> str:
        """JavaScript 出力を組み立てる。"""
        return f'''{self.config.file_header}

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const {{ spawnSync }} = require("node:child_process");

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH = "{display_path}";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE = {source_literal};

/**
 * Python インタプリタで埋め込みソースを実行する。
 * @param {{ interpreter: string, scriptPath: string, args: string[] }} params 実行パラメータ。
 * @returns {{ status: number|null, error?: Error }} 実行結果。
 */
function runPython(params) {{
  const env = {{ ...process.env }};
  const current = env.PYTHONPATH;
  env.PYTHONPATH = current && current.length > 0
    ? ["src", current].join(path.delimiter)
    : "src";
  return spawnSync(params.interpreter, [params.scriptPath, ...params.args], {{
    stdio: "inherit",
    env,
  }});
}}

/** エントリポイント。 */
function main() {{
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "pytra_js_"));
  const scriptPath = path.join(tempDir, "embedded.py");
  fs.writeFileSync(scriptPath, PYTRA_SOURCE_CODE, {{ encoding: "utf8" }});

  let result = runPython({{ interpreter: "python3", scriptPath, args: process.argv.slice(2) }});
  if (result.error && result.error.code === "ENOENT") {{
    result = runPython({{ interpreter: "python", scriptPath, args: process.argv.slice(2) }});
  }}

  fs.rmSync(tempDir, {{ recursive: true, force: true }});
  if (result.error) {{
    console.error("error: python interpreter not found (python3/python)");
    process.exit(1);
  }}
  process.exit(typeof result.status === "number" ? result.status : 1);
}}

main();
'''

    def _render_typescript(self, source_literal: str, display_path: str) -> str:
        """TypeScript 出力を組み立てる。"""
        return f'''{self.config.file_header}

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {{ spawnSync, SpawnSyncReturns }} from "node:child_process";

/** 埋め込み元 Python ファイルパス。 */
const PYTRA_SOURCE_PATH: string = "{display_path}";
/** 埋め込み Python ソースコード。 */
const PYTRA_SOURCE_CODE: string = {source_literal};

/**
 * Python インタプリタで埋め込みソースを実行する。
 * @param interpreter 実行する Python コマンド名。
 * @param scriptPath 一時生成した Python ファイルパス。
 * @param args Python 側へ渡すコマンドライン引数。
 * @returns 同期実行結果。
 */
function runPython(interpreter: string, scriptPath: string, args: string[]): SpawnSyncReturns<Buffer> {{
  const env: NodeJS.ProcessEnv = {{ ...process.env }};
  const current = env.PYTHONPATH;
  env.PYTHONPATH = current && current.length > 0
    ? ["src", current].join(path.delimiter)
    : "src";
  return spawnSync(interpreter, [scriptPath, ...args], {{
    stdio: "inherit",
    env,
  }});
}}

/** エントリポイント。 */
function main(): void {{
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "pytra_ts_"));
  const scriptPath = path.join(tempDir, "embedded.py");
  fs.writeFileSync(scriptPath, PYTRA_SOURCE_CODE, {{ encoding: "utf8" }});

  let result = runPython("python3", scriptPath, process.argv.slice(2));
  if (result.error && (result.error as NodeJS.ErrnoException).code === "ENOENT") {{
    result = runPython("python", scriptPath, process.argv.slice(2));
  }}

  fs.rmSync(tempDir, {{ recursive: true, force: true }});
  if (result.error) {{
    console.error("error: python interpreter not found (python3/python)");
    process.exit(1);
  }}
  process.exit(typeof result.status === "number" ? result.status : 1);
}}

main();
'''
