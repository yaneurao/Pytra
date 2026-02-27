# py2cpp サポートマトリクス（テスト準拠）

<a href="../../../en/language/cpp/spec-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


最終更新: 2026-02-22

この文書は、`src/py2cpp.py` の言語機能サポート状況を「実装コード」と「実行テスト」の両方で確認できる粒度でまとめたものです。

## ステータス定義

- `supported`: 現行でサポート。対応テストが green。
- `partial`: 一部条件つきでサポート。制約あり。
- `unsupported`: 現行で非対応。明示的にエラー化。
- `not_yet_verified`: 仕様文書にはあるが、専用回帰テストが不足しており本表では未確定。

## コア構文・式

| 機能 | ステータス | 現状 | 根拠 |
|---|---|---|---|
| `enumerate(xs)` | supported | サポート済み。 | `src/py2cpp.py:3304`, `test/unit/test_py2cpp_features.py:1441`, `test/fixtures/strings/enumerate_basic.py:7` |
| `enumerate(xs, 1)` / `enumerate(xs, start)` | supported | 第2引数つきサポート済み。`start` は `int64` へ変換される。 | `src/py2cpp.py:3306`, `test/fixtures/strings/enumerate_basic.py:17`, `test/fixtures/strings/enumerate_basic.py:21`, `test/unit/test_py2cpp_features.py:1441` |
| `lambda` 基本（0引数/1引数/複数引数） | supported | サポート済み。 | `src/py2cpp.py:4296`, `test/unit/test_py2cpp_features.py:1259`, `test/fixtures/core/lambda_basic.py:8` |
| `lambda` の外側変数キャプチャ | supported | サポート済み（`[&]` キャプチャ）。 | `src/py2cpp.py:4303`, `test/unit/test_py2cpp_features.py:1337`, `test/fixtures/core/lambda_capture_multiargs.py:7` |
| `lambda` を引数として渡す | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:1349`, `test/fixtures/core/lambda_as_arg.py:10` |
| `lambda` の即時呼び出し | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:1355`, `test/fixtures/core/lambda_immediate.py:5` |
| `lambda` 内の三項演算子 | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:1331`, `test/fixtures/core/lambda_ifexp.py:6` |
| `x if cond else y`（IfExp） | supported | サポート済み。 | `src/py2cpp.py:3911`, `test/unit/test_py2cpp_features.py:964` |
| `list` 内包表記 | partial | サポート済み。ただし generator は 1 個前提。 | `src/py2cpp.py:4304`, `src/py2cpp.py:4306`, `test/unit/test_py2cpp_features.py:1253`, `test/unit/test_py2cpp_features.py:1325` |
| `set` 内包表記 | partial | サポート済み。ただし generator は 1 個前提。 | `src/py2cpp.py:4381`, `src/py2cpp.py:4383`, `test/unit/test_py2cpp_features.py:1307`, `test/fixtures/collections/comprehension_dict_set.py:6` |
| `dict` 内包表記 | partial | サポート済み。ただし generator は 1 個前提。 | `src/py2cpp.py:4436`, `src/py2cpp.py:4438`, `test/unit/test_py2cpp_features.py:1307`, `test/fixtures/collections/comprehension_dict_set.py:7` |
| 内包表記の `if` 条件 | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:1253`, `test/unit/test_py2cpp_features.py:1301`, `test/fixtures/collections/comprehension_filter.py:7` |
| 内包表記で `range(start, stop, step)` | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:1325`, `test/fixtures/collections/comprehension_range_step.py:6` |
| ネスト内包（内包の中に内包） | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:1295`, `test/fixtures/collections/comprehension_nested.py:6` |
| `str` スライス | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:1435`, `test/fixtures/strings/str_slice.py:1` |
| 文字列の for-each | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:1429`, `test/fixtures/strings/str_for_each.py:1` |
| `bytes` / `bytearray` 基本操作 | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:1241`, `test/unit/test_py2cpp_features.py:1247`, `test/fixtures/typing/bytes_basic.py:1`, `test/fixtures/typing/bytearray_basic.py:1` |

## import / モジュール解決

| 機能 | ステータス | 現状 | 根拠 |
|---|---|---|---|
| `import M` | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:1385`, `test/fixtures/imports/import_math_module.py:3` |
| `import M as A` | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:259`, `test/fixtures/imports/import_pytra_runtime_png.py:3` |
| `from M import S` | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:242`, `test/unit/test_py2cpp_features.py:1283`, `test/fixtures/imports/from_import_symbols.py:3` |
| `from M import S as A` | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:1283`, `test/fixtures/imports/from_import_symbols.py:3` |
| 循環 import 検出 | unsupported | 検出して `input_invalid(kind=import_cycle)` で停止。 | `src/py2cpp.py:5734`, `test/unit/test_py2cpp_features.py:567` |
| 相対 import（`from .m import x`） | unsupported | `input_invalid(kind=unsupported_import_form)`。 | `src/py2cpp.py:4693`, `test/unit/test_py2cpp_features.py:596` |
| `from M import *` | partial | wildcard import を受理して変換継続。静的な公開シンボル検証は限定的。 | `src/pytra/compiler/east_parts/core.py:4427`, `src/py2cpp.py:6322`, `tools/check_yanesdk_py2cpp_smoke.py:1` |
| 未解決モジュール import | unsupported | `input_invalid(kind=missing_module)`。 | `test/unit/test_py2cpp_features.py:544` |
| import 束縛重複 | unsupported | `input_invalid(kind=duplicate_binding)`。 | `test/unit/test_py2cpp_features.py:645`, `test/unit/test_py2cpp_features.py:675` |
| `from M import S` 後の `M.T` 参照 | unsupported | `input_invalid(kind=missing_symbol)` 扱い。 | `test/unit/test_py2cpp_features.py:732` |

## OOP / 型 / ランタイム

| 機能 | ステータス | 現状 | 根拠 |
|---|---|---|---|
| `super().__init__()` | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:1379`, `test/fixtures/oop/super_init.py:1` |
| `@dataclass` | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:1519`, `test/fixtures/stdlib/dataclasses_extended.py:1` |
| `Enum` / `IntEnum` / `IntFlag` | supported | サポート済み。 | `test/unit/test_py2cpp_features.py:1453`, `test/unit/test_py2cpp_features.py:1459`, `test/unit/test_py2cpp_features.py:1465` |
| `Any` 系（基本） | supported | サポート済み（`Any`/`None`/混在 list/dict を回帰確認）。 | `test/unit/test_py2cpp_features.py:1265`, `test/unit/test_py2cpp_features.py:1271`, `test/unit/test_py2cpp_features.py:1277`, `test/unit/test_py2cpp_features.py:1289` |
| `object` レシーバへの属性/メソッド呼び出し | unsupported | emit guard で拒否。 | `test/unit/test_py2cpp_features.py:1531` |

## CLI オプション由来の制約

| 機能 | ステータス | 現状 | 根拠 |
|---|---|---|---|
| `--str-index-mode=codepoint` | unsupported | 現状は明示エラー。 | `src/pytra/compiler/transpile_cli.py:152`, `test/unit/test_py2cpp_features.py:1183` |
| `--str-slice-mode=codepoint` | unsupported | 現状は明示エラー。 | `src/pytra/compiler/transpile_cli.py:154`, `src/py2cpp.py:6419` |
| `--int-width=bigint` | unsupported | 変換実行では明示エラー。`--dump-options` での計画値表示のみ許可。 | `src/pytra/compiler/transpile_cli.py:144`, `test/unit/test_py2cpp_features.py:1167`, `src/py2cpp.py:6417` |

## 未確定（本表で過剰断定しない項目）

次は専用回帰テストの網羅が不足しており、現時点では `not_yet_verified` 扱いにします。

- 関数引数の default 値、`*args`、`**kwargs` の詳細な互換範囲
- `yield` / generator expression の挙動
- 例外階層の細かな互換（例: 複数 except 節の型パターン）

## 更新ルール

- この表を更新するときは、対応行に「実行テストの根拠（`test/unit/...`）」を必ず追加する。
- 「実装上は通るがテスト根拠がない」ものは `supported` にしない。
