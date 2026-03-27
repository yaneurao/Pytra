<a href="../../en/tutorial/advanced-usage.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# 発展的な使い方

このページは、[how-to-use.md](./how-to-use.md) には載せない高度な変換ルートと runtime helper 注釈（主に `@abi`）をまとめたものです。

## C++ max-opt route

- `./pytra ... --target cpp --codegen-opt 3` は、C++ compat route ではなく linked-program optimizer を通す max route です。
- `--build` を併用すると、linked-program 最適化後の multi-file output から `Makefile` 生成と build を続けて実行します。
- 中間の linked bundle は `--output-dir/.pytra_linked/` に置きます。
- `--codegen-opt 0/1/2` は従来 route を維持します。
- route 変更の非退行確認は、representative CLI test だけでなく sample parity でも見る前提です。

```bash
./pytra sample/py/18_mini_language_interpreter.py \
  --target cpp \
  --codegen-opt 3 \
  --build \
  --output-dir out/sample18_maxopt \
  --opt -O3 \
  --exe sample18.out
```

確認コマンド:

```bash
python3 tools/runtime_parity_check.py \
  --targets cpp \
  --case-root sample \
  --all-samples \
  --cpp-codegen-opt 3 \
  --east3-opt-level 2
```

## runtime helper での `@abi`

- `@abi` は runtime helper の境界 ABI を固定するための注釈です。一般 user code へ広げる前提ではありません。
- canonical mode は `args` 側が `default` / `value` / `value_mut`、`ret` 側が `default` / `value` です。
- 引数側 `value` は read-only value ABI を意味します。旧 `value_readonly` は移行期 alias で、metadata では `value` に正規化されます。

```python
from pytra.std import abi

@abi(args={"parts": "value"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    ...
```

## `pytra-cli.py` / `pytra-cli.py` の使い分け

- 通常実行は `src/pytra-cli.py` を使います。target backend は必要言語のみ lazy import されます。
- selfhost 実行は `src/pytra-cli.py` を使います。backend は static eager import 固定です。
- 既存 `py2{lang}.py` ラッパは移行互換用途のみで、通常運用の入口は `pytra-cli.py` / `pytra-cli.py` に統一します。

```bash
# 通常実行（host-lazy）
python3 src/pytra-cli.py test/fixtures/core/add.py --target rs -o out/add.rs

# selfhost 実行（static eager import）
python3 src/pytra-cli.py test/fixtures/core/add.py --target rs -o out/add_selfhost.rs
```

### 移行メモ（`py2*.py` 互換ラッパ）

- 既存の `py2rs.py`, `py2js.py`, `py2rb.py` などは非推奨の互換ラッパです。
- 正規運用は `pytra-cli.py --target <lang>` を唯一の入口とし、互換ラッパは段階撤去対象として扱います。
- 層別 option（`--lower-option`, `--optimizer-option`, `--emitter-option`）は `pytra-cli.py` 側仕様で統一しています。

```bash
# 正規入口（推奨）
python3 src/pytra-cli.py test/fixtures/core/add.py --target rs -o out/add_py2x.rs
```

## `toolchain/emit/cpp.py` / `toolchain/emit/all.py`（EAST3 JSON -> target backend）

- `toolchain/emit/cpp.py` は C++ backend の独立エントリポイントです。`manifest.json` を入力として C++ multi-file 出力を生成します。非 C++ backend を import しないため、起動が高速です。
- `toolchain/emit/all.py` は全 backend 対応の汎用エントリポイントです。`EAST3(JSON)` から直接 backend を実行します。
- backend 単体回帰や、`test/ir` の固定IR検証で使います。
- 入力は `.json` のみ受理し、`east_stage=3` 以外は fail-fast します。

```bash
# 1) .py から EAST3(JSON) fixture を作成
python3 src/pytra-cli.py sample/py/01_mandelbrot.py --target cpp \
  -o work/tmp/seed_01.cpp --dump-east3-after-opt work/tmp/01_mandelbrot.east3.json

# 2) EAST3(JSON) から直接ターゲット言語へ変換
python3 src/toolchain/emit/all.py work/tmp/01_mandelbrot.east3.json --target rs \
  -o work/tmp/east2x_01.rs --no-runtime-hook

# 3) 主要 target（cpp/rs/js）の backend-only smoke
python3 tools/check_east2x_smoke.py
```

補足:
- `--lower-option key=value` / `--optimizer-option key=value` / `--emitter-option key=value` を `toolchain/emit/all.py` でも利用できます。
- `--no-runtime-hook` を外すと、target ごとの runtime 補助ファイル配置も含めて確認できます。

## linked-program の dump / link-only / emit

- linked-program の正規パイプラインは `pytra-cli.py --link-only` → `toolchain/emit/cpp.py`（C++ の場合）です。
- `pytra-cli.py --dump-east3-dir DIR` は raw `EAST3` 群と `link-input.json` を `DIR` に書き出して終了します。
- `pytra-cli.py --link-only --output-dir DIR` は backend 生成を行わず、`manifest.json` と linked module 群だけを `DIR` に書き出します。
- `toolchain/emit/cpp.py` は `manifest.json` を読み込んで C++ multi-file 出力を生成します。
- `toolchain/emit/all.py` は全 backend 対応の汎用経路として引き続き利用できます。

```bash
# 1) .py から raw EAST3 群と link-input.json を出力
python3 src/pytra-cli.py sample/py/18_mini_language_interpreter.py --target cpp \
  --dump-east3-dir out/linked_debug/raw

# 2) compile + link + optimize して linked output を作る
PYTHONPATH=src python3 src/pytra-cli.py sample/py/18_mini_language_interpreter.py \
  --target cpp --link-only --output-dir out/linked_debug/linked

# 3) linked output から C++ emit（toolchain/emit/cpp.py — C++ backend のみ import）
PYTHONPATH=src python3 src/toolchain/emit/cpp.py out/linked_debug/linked/manifest.json \
  --output-dir out/linked_debug/cpp

# 4) toolchain/emit/all.py で全 backend 対応の汎用経路を使うこともできる
python3 src/toolchain/emit/all.py out/linked_debug/linked/manifest.json --target cpp \
  --output-dir out/linked_debug/cpp_east2x
```

補足:
- linked-program の global pass は、manifest が列挙した module 群だけを入力に使います。`source_path` を辿った追加読込で import closure を広げることはしません。
- `NonEscapeInterproceduralPass` は linked-program 経路では linker が埋めた `meta.non_escape_import_closure` だけを見ます。closure が不足している場合は fail-closed で unresolved 扱いになります。
