<a href="../../ja/plans/p0-math-stdlib-runtime-annotation.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-math-stdlib-runtime-annotation.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-math-stdlib-runtime-annotation.md`

# P0-24: import モジュール属性呼び出し（math.* 等）の EAST3 runtime annotation 付与

最終更新: 2026-03-24

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MATH-STDLIB-ANNOTATION`

## 背景

`from pytra.std import math` + `math.sqrt(x)` のような import モジュール属性呼び出しで、EAST3 の Call ノードに `semantic_tag` / `runtime_module_id` / `runtime_call` が設定されない。

経緯:
1. 以前は EAST1 パーサー内で `_sh_annotate_noncpp_attr_call_expr` を呼んで `noncpp_module_id` / `noncpp_runtime_call` を埋め込んでいた
2. 2026-03-21 に P2-REMOVE-NONCPP-RUNTIME-CALL で「EAST1 の責務逸脱」として除去された
3. `_sh_annotate_noncpp_attr_call_expr` は定義だけ残り、どこからも呼ばれなくなった
4. C++ emitter は生の `attr` 名 + `_resolve_imported_module_name` で独自に math を再解決しているが、これは EAST3 仕様が禁止する「emitter が生 AST ノード依存の再解決をする」パターン
5. Rust 担当から「math.sqrt(int) に int→float Cast がない」と報告。cast 挿入自体は `resolved_type == "float64"` フォールバックで動作するが、semantic_tag 未設定により `_FLOAT_STDLIB_SEMANTIC_TAGS` チェックが空振りしている

## 影響

- 全 backend の math.* 呼び出しで `semantic_tag` / `runtime_module_id` / `runtime_symbol` が空
- 非 C++ emitter は EAST3 解決済み属性を正本として参照するため、math 関数の dispatch ができない
- cast 挿入は `resolved_type` フォールバックで動くが、semantic_tag ベースのチェックが機能していない

## 対象

EAST2→EAST3 lowering で import モジュール属性 Call に runtime annotation を設定する。

## 非対象

- C++ emitter の生 attr 名再解決の除去（段階的に別タスクで対応）
- `_sh_annotate_noncpp_attr_call_expr` / `_sh_lookup_noncpp_attr_runtime_call` の除去（今回は活用する側）

## 受け入れ基準

1. `math.sqrt(x)` (x: int64) の EAST3 Call ノードに `runtime_module_id: "pytra.std.math"`, `runtime_symbol: "sqrt"`, `semantic_tag: "stdlib.method.sqrt"` が設定される
2. 全 math 関数（sin, cos, tan, sqrt, exp, log, log10, fabs, floor, ceil, pow）で同様に設定される
3. int 引数に対する cast 挿入が `_FLOAT_STDLIB_SEMANTIC_TAGS` チェック経由でも機能する
4. `python3 tools/check/check_py2cpp_transpile.py` が通る
5. 既存テストにリグレッションがない

## 子タスク

- [x] [ID: P0-MATH-STDLIB-ANNOTATION-S1] `_apply_attr_call_expr_annotation` で owner が import module の場合に `_sh_annotate_noncpp_attr_call_expr` を呼ぶ配線を追加する
- [x] [ID: P0-MATH-STDLIB-ANNOTATION-S2] テスト追加 + 既存テストのリグレッションがないことを検証する

## 決定ログ

- 2026-03-24: Rust 担当の報告（math.sqrt(int) の cast 欠落）を起点に調査。cast 挿入は resolved_type フォールバックで動作するが、semantic_tag / runtime_module_id の未設定が本質的問題と判断。EAST2→EAST3 lowering での annotation 付与を P0 で起票。
- 2026-03-24: S1 完了。変更 2 ファイル: (1) `core_expr_attr_call_annotation.py` — `_apply_attr_call_expr_annotation` に import module 判定 `_is_import_module_attr_call` を追加し、noncpp 経路へ配線。(2) `core_runtime_call_semantics.py` — `_sh_annotate_noncpp_attr_call_expr` 内で `lookup_runtime_binding_semantic_tag` が空の場合に `lookup_stdlib_method_semantic_tag` へフォールバック追加。
- 2026-03-24: S2 完了。検証結果: math.sqrt(int) → `runtime_module_id=pytra.std.math`, `runtime_symbol=sqrt`, `semantic_tag=stdlib.method.sqrt`, `resolved_runtime_call=math.sqrt`, `casts=[int64→float64]`。全 18 sample EAST3 生成 OK。C++ transpile はベースラインと同一。
