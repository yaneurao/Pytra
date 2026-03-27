<a href="../../ja/plans/p4-preexisting-test-failures-fix.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p4-preexisting-test-failures-fix.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p4-preexisting-test-failures-fix.md`

# P4: pre-existing テスト失敗の修正

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P4-PREEXISTING-TEST-FAILURES-FIX-01`

## 背景

`test/unit/toolchain/emit/cpp/test_py2cpp_features.py` に 4 件の pre-existing テスト失敗がある。
これらは今セッション以前から存在しており、変更前のコードでも同様に失敗する。

確認済みの失敗テスト:
- `test_runtime_module_class_signature_lookup_is_repo_root_independent`
- `test_runtime_special_ops_emit_direct_built_in_headers`
- `test_sys_extended_runtime`
- `test_transpile_cli_load_east3_typed_wrapper_wraps_legacy_doc`

## 対象

- `test/unit/toolchain/emit/cpp/test_py2cpp_features.py` — 4 件の失敗テスト
- 関連する emitter / runtime コード

## 受け入れ基準

- 4 件の pre-existing テスト失敗がすべて解消されている。
- 他のテストに退行がないこと。

## 決定ログ

- 2026-03-19: セッション中に pre-existing failures として確認。起票。
