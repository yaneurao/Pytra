<a href="../../ja/plans/p4-vararg-east3-lowering.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p4-vararg-east3-lowering.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p4-vararg-east3-lowering.md`

# P4: `*args` vararg サポート — EAST3 レベル脱糖

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P4-VARARG-EAST3-LOWERING-01`

## 背景

現在 Pytra は `*args: T` 形式の型付き可変長引数をパーサーレベルで受け付け、C++ バックエンドのみがそれをサポートしている。他の全バックエンド（Rust, Go, Java, JS, TS, C#, Ruby, Kotlin, Swift, Scala, Lua, PHP, Nim, PowerShell）は `reject_backend_typed_vararg_signatures()` で即 reject する。

目標: EAST3 のローリング段で `*args: T` を `args: list[T]` に脱糖し、呼び出し側も `f(a,b,c)` → `f([a,b,c])` に変換する。これにより全バックエンドで変更ゼロでvarargが動く。

## 設計

### 脱糖方針

1. **FunctionDef 変換**: `vararg_name`/`vararg_type` を取り除き、`vararg_name: list[vararg_type]` を通常引数として `arg_order` / `arg_types` に追加する。マーカー `vararg_desugared_v1: {n_fixed, elem_type, vararg_name}` をノードに付与する（グローバルフェーズで利用）。

2. **呼び出し側変換（モジュール内）**: EAST3 per-module ローリング後、同一モジュール内の Call ノードを走査する。`func.id` または `func.attr` がローカル vararg 関数テーブルにマッチする場合、trailing args を `List` ノードへパックする。

3. **呼び出し側変換（クロスモジュール）**: `global_optimizer.py` の `optimize_linked_program` 内で全モジュールの `vararg_desugared_v1` マーカーを集めた後、全 Call ノードを走査して同様のパッキングを実施する。

### マッチング戦略

- 直接呼び出し (`func.kind == "Name"`, `func.id == fn_name`): ローカルテーブルで一致照合
- メソッド呼び出し (`func.kind == "Attribute"`, `func.attr == method_name`): ローカル/グローバルテーブルで一致照合
- クロスモジュール直接呼び出し: `meta.non_escape_callsite.callee == "module_id::fn_name"` で照合

### pathlib 拡張

`joinpath(*parts: str | Path) -> Path` を `pytra/std/pathlib.py` に追加する。

## 非対象

- untyped `*args`（型なし可変長引数）はサポートしない（既存の `ng_varargs.py` fixture と同様）
- keyword `**kwargs` はスコープ外
- 関数ポインタ経由の呼び出しはスコープ外

## 受け入れ基準

1. `test/fixtures/signature/ok_typed_varargs_representative.py` が全バックエンドで transpile できる（C++ 以外も reject しない）
2. `Path.joinpath(a, b, c)` が `Path([a, b, c])` 相当に変換され、全バックエンドでビルドできる
3. `reject_backend_typed_vararg_signatures()` が全モジュール走査後にエラーを出さない

## 実装ステップ

- S1: `east2_to_east3_lowering.py` に post-pass 追加（FunctionDef 変換 + モジュール内 Call パッキング）
- S2: `global_optimizer.py` に `_apply_vararg_callsite_packing_global` 追加（クロスモジュール Call パッキング）
- S3: `pytra/std/pathlib.py` に `joinpath(*parts: str | Path) -> Path` 追加
- S4: テスト実行・検証

## 決定ログ

- 2026-03-21: EAST3 post-pass 方式を採用。per-module ローリング後に 2 回走査（FunctionDef 変換 → Call パッキング）。グローバルフェーズで cross-module Call パッキング。バックエンド変更ゼロを目標とする。
