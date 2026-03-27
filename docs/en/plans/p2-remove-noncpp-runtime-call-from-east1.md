<a href="../../ja/plans/p2-remove-noncpp-runtime-call-from-east1.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p2-remove-noncpp-runtime-call-from-east1.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p2-remove-noncpp-runtime-call-from-east1.md`

# P2: EAST1 パーサーから noncpp_runtime_call / noncpp_module_id を除去

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-REMOVE-NONCPP-RUNTIME-CALL`

## 背景

EAST1 パーサー（`core_expr_resolution_semantics.py`）が `_sh_lookup_noncpp_attr_runtime_call` を呼び、`math.sqrt()` 等の import モジュール属性アクセスに対して `noncpp_module_id` / `noncpp_runtime_call` を EAST1 ノードに埋め込んでいる。

しかし:

1. **どの emitter もこのフィールドを読んでいない** — `src/toolchain/emit/` に `noncpp_runtime_call` / `noncpp_module_id` の参照はゼロ
2. **emitter は独自に解決している** — `resolve_attribute_owner_context` → `_resolve_imported_module_name` → `_lookup_module_attr_runtime_call` で、EAST ノードの `import_module_bindings` と emitter 固有テーブルから独立に解決
3. **EAST1 の責務を逸脱している** — モジュール関数のランタイム呼び出し解決は EAST1（構文解析 + 型推論）の責務ではない
4. **forbidden ガードとの衝突を引き起こしている** — `_is_forbidden_object_receiver_type("unknown")` が import モジュール名に対して発火し、31 件のリグレッションを生んでいる（`d8926b03e` で `unknown` を forbidden に追加した副作用）

## 対象

| ファイル | 変更内容 |
|---|---|
| `core_expr_resolution_semantics.py` | `_sh_lookup_noncpp_attr_runtime_call` 呼び出しと `noncpp_module_id` / `noncpp_runtime_call` フィールドの生成を除去 |
| `core_expr_attr_subscript_annotation.py` | `noncpp_module_id` / `noncpp_runtime_call` の伝播ロジックを除去 |
| `core_runtime_call_semantics.py` | `_sh_lookup_noncpp_attr_runtime_call` / `_sh_annotate_noncpp_attr_call_expr` 関数を除去（呼び出し元が消えるため） |
| `core_expr_attr_call_annotation.py` | `_sh_annotate_noncpp_attr_call_expr` 呼び出しを除去 |

## 非対象

- emitter 側の `_lookup_module_attr_runtime_call` — 正当な emitter 責務であり残す
- `_SH_IMPORT_MODULES` のグローバル状態 — 他の用途があるため残す
- `_is_forbidden_object_receiver_type` の `unknown` 除外 — この修正により import モジュール名が `unknown` として forbidden に引っかかる問題は根本解消されるが、forbidden ガード自体に import module スキップが必要かは別途確認

## 受け入れ基準

- [ ] EAST1 ノードに `noncpp_module_id` / `noncpp_runtime_call` が含まれなくなる
- [ ] 全 emitter の既存テストがリグレッションしない
- [ ] `d8926b03e` で発生した 31 件のリグレッション（import モジュール属性アクセスの forbidden 拒否）が解消される

## 子タスク

- [x] [ID: P2-REMOVE-NONCPP-RUNTIME-CALL-01] `core_expr_resolution_semantics.py` から `noncpp_*` フィールド生成を除去する
- [x] [ID: P2-REMOVE-NONCPP-RUNTIME-CALL-02] `core_expr_attr_subscript_annotation.py` から `noncpp_*` 伝播ロジックを除去する
- [x] [ID: P2-REMOVE-NONCPP-RUNTIME-CALL-03] `core_runtime_call_semantics.py` / `core_expr_attr_call_annotation.py` から不要関数を除去する
- [x] [ID: P2-REMOVE-NONCPP-RUNTIME-CALL-04] 既存テストのリグレッションがないことを検証する

## 決定ログ

- 2026-03-21: P0-19（block-scope hoist）作業中に 31 件のリグレッションを調査。Julia backend 担当が `d8926b03e` の forbidden ガード追加と import モジュール型未登録の衝突を特定。調査の結果、EAST1 の `_sh_lookup_noncpp_attr_runtime_call` が埋め込む `noncpp_*` フィールドはどの emitter からも参照されていない死にコードであり、EAST1 の責務を逸脱した実装と判断。除去を起票。
- 2026-03-21: S1〜S4 完了。4ファイルから `noncpp_*` 関連コード（2関数、伝播ロジック、import）を除去。`_resolve_attr_expr_owner_state` の forbidden ガードに `_SH_IMPORT_MODULES` スキップを追加し、import モジュール名が `unknown` として拒否される問題を解消。tuple 型注釈を 7→5 要素に縮小。既存テスト 80 passed / 40 failed（ベースラインと同一、リグレッションなし）。
