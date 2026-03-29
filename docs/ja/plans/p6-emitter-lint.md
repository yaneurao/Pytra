<a href="../../en/plans/p6-emitter-lint.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P6-EMITTER-LINT: emitter 責務違反チェッカーの新設

最終更新: 2026-03-30
ステータス: 未着手

## 背景

emitter は EAST3 の情報だけを使ってコードを生成すべきだが（spec-emitter-guide §1）、歴史的にモジュール名や runtime 関数名をハードコードしている箇所がある。toolchain1 の C++ emitter は debt が多かったが、toolchain2 では C++ emitter を丸ごと書き直しているため、debt は存在しない。

これらの責務違反は parity check では検出できない（ハードコードでも正しい名前なら動いてしまう）。emitter ソースコード自体を grep して違反を検出するチェッカーが必要。

## 検出対象（6カテゴリ）

### 1. モジュール名のハードコード

emitter が `runtime_module_id` ではなくモジュール名を文字列で知っている。

禁止パターン例: `"math"`, `"pathlib"`, `"json"`, `"sys"`, `"os"`, `"glob"`, `"time"`, `"subprocess"`, `"re"`, `"argparse"`

### 2. runtime 関数名のハードコード

emitter が `runtime_call` / `runtime_symbol` ではなく関数名を直接知っている。

禁止パターン例: `"perf_counter"`, `"py_len"`, `"py_print"`, `"py_range"`, `"write_rgb_png"`, `"save_gif"`, `"grayscale_palette"`

### 3. ターゲット言語の定数/関数名のハードコード

mapping.json の `calls` テーブルの責務を emitter が横取りしている。

禁止パターン例: `"M_PI"`, `"M_E"`, `"std::sqrt"`, `"std::stoll"`, `"math.Sqrt"`, `"Math.PI"`

### 4. runtime プレフィックスマッチ

`runtime_call_adapter_kind` で判定すべきところをモジュール ID のプレフィックスで分岐している。

禁止パターン例: `"pytra.std."`, `"pytra.core."`, `"pytra.built_in."`

### 5. クラス名のハードコード

EAST3 の型情報から来るべき判定を emitter がクラス名で分岐している。

禁止パターン例: `"Path"`, `"ArgumentParser"`, `"Exception"`

### 6. Python 構文の残留

EAST3 では既に正規化済みの Python 構文が emitter に残っている。

禁止パターン例: `"__main__"`, `"super()"`

## 設計

### grep ベースの静的検査

`src/toolchain2/emit/*/` 配下の `.py` ファイルを対象に、禁止パターンの文字列を grep する。

- 検出精度が高いカテゴリ（1〜4, 一部の 5, 6）に絞る
- カテゴリ 4〜7（型名の文字列マッチ、属性名での分岐等）は誤検知が多いため、将来 AST ベースの lint に移行する候補とする

### allowlist

~~C++ emitter の allowlist~~ — **不要**: toolchain2 の C++ emitter は書き直しのため既存違反がなく、allowlist は作成しない。チェッカーは全違反を違反マトリクスに記録する（exit code には影響しない）。

### 出力形式

言語 × カテゴリのマトリクスを stdout に出力する:

```
| カテゴリ | cpp | go | rs | ts |
|---|---|---|---|---|
| module name | 🟥3 | 🟩0 | 🟩0 | 🟩0 |
| runtime symbol | 🟥5 | 🟥1 | 🟩0 | 🟩0 |
| target constant | 🟥2 | 🟩0 | 🟩0 | 🟩0 |
| prefix match | 🟥1 | 🟩0 | 🟩0 | 🟩0 |
| class name | 🟥2 | 🟩0 | 🟩0 | 🟩0 |
| Python syntax | 🟩0 | 🟩0 | 🟩0 | 🟩0 |
```

この出力を進捗ページの一部として利用可能にする。

### 既存チェッカーとの関係

| 既存チェッカー | カバー範囲 | 本チェッカーとの関係 |
|---|---|---|
| `check_emitter_runtimecall_guardrails.py` | runtime call 名の直書き（non-C++ のみ） | カテゴリ 2 と重なるが、本チェッカーは全言語対象 |
| `check_emitter_forbidden_runtime_symbols.py` | `__pytra_*` 等の実装シンボル | カテゴリ 2 の一部と重なる |

将来的には本チェッカーに統合し、既存の2本は廃止してよい。

## 決定ログ

- 2026-03-30: grep ベースで6カテゴリの責務違反を検出する方針に決定。型名の文字列マッチ（`resolved_type == "list"` 等）や属性名での分岐（`attr == "append"` 等）は誤検知が多いため、grep ベースの検出対象から除外。将来 AST ベースの lint に移行する候補とする。
- 2026-03-30: `run_local_ci.py` への組み込みではなく、`runtime_parity_check.py` のついでに実行する方針に変更。違反は違反マトリクスに記録するだけで、parity check の exit code には影響しない。各 backend が parity check を日常的に回しているため、実質的なカバレッジが高い。
