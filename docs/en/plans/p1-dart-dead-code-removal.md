<a href="../../ja/plans/p1-dart-dead-code-removal.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p1-dart-dead-code-removal.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p1-dart-dead-code-removal.md`

# P1: Dart emitter デッドコード除去

## 背景

spec-emitter-guide.md 準拠のリファクタリングにより、Dart emitter の import 生成と `@extern` 委譲が `resolve_import_binding_doc` + `__native` パターンに移行された。旧方式で使用していたハードコード関数群がデッドコードとして残存しており、§1（モジュール ID ハードコード禁止）違反の温床となっている。

## 対象

- `_runtime_symbol_alias_expr()` — ハードコードされた runtime symbol → Dart 式のマッピング（約50行）
- `_runtime_module_alias_line()` — ハードコードされた module_id → Dart import 行のマッピング
- `_runtime_symbol_alias_line()` — ハードコードされた symbol → Dart alias 行のマッピング
- `_is_math_runtime_symbol()` — math モジュール判定
- `_is_perf_counter_runtime_symbol()` — perf_counter 判定
- `_is_glob_runtime_symbol()` — glob 判定
- `_is_os_runtime_symbol()` — os 判定
- `_is_os_path_runtime_symbol()` — os_path 判定
- `_is_sys_runtime_symbol()` — sys 判定
- `_runtime_module_symbol_names()` — runtime module symbols 一覧取得
- `_runtime_symbol_call_adapter_kind()` — call adapter 判定
- `_runtime_symbol_semantic_tag()` — semantic tag 判定
- `_pascal_symbol_name()` — PascalCase 変換（上記関数でのみ使用）
- `_is_compile_time_std_import_symbol()` — compile-time symbol 判定（新方式ではインラインで処理済み）

## 非対象

- `_safe_ident()` — 引き続き使用中
- `_binop_symbol()` / `_cmp_symbol()` — 引き続き使用中
- `_dart_string()` — 引き続き使用中
- `_collect_relative_import_name_aliases()` — `_scan_module_symbols` で使用中（§7 の `build_import_alias_map` 完全移行は別タスク）

## 受け入れ基準

1. 上記関数をすべて削除する。
2. 削除後、sample/py 全 18 ケースが Dart でバイナリ一致する。
3. `_COMPILETIME_STD_IMPORT_SYMBOLS` 定数は残存してよい（新方式でも参照するため）。

## 決定ログ

- 2026-03-23: 計画書作成。
