# P2: EAST 解決情報 + CodeEmitter 依存収集による最小 import 生成

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-EAST-IMPORT-RESOLUTION-01`

背景:
- 一部 backend では `import` / `using` / `#include` を固定文字列で常時出力しており、未使用依存回避のダミーコード（例: Go の `var _ = math.Pi`）が必要になっている。
- 依存確定は現状 emitter ごとに分散しており、言語間で実装方針が揃っていない。
- `CodeEmitter` 基底には `meta.import_bindings` / `qualified_symbol_refs` を読む仕組みがあるが、ノード単位解決情報と import 収集の共通 API までは未整備。

目的:
- EAST レベルで「識別子/呼び出しがどの import 由来か」を保持し、CodeEmitter 基底で依存モジュールを集約する。
- 各言語 emitter は「依存キー→言語固有 import 文」のマッピングのみ担当し、最小 import を共通方針で生成する。

対象:
- EAST3 ノード属性または side table への import 解決情報付与
- `src/pytra/compiler/east_parts/code_emitter.py` の依存収集 API（register/finalize）
- 各 backend emitter の import 出力経路（固定 import の撤去対象洗い出しと段階移行）
- import 回帰テスト（未使用 import 禁止、必要 import のみ出力）

非対象:
- 画像 runtime / 数値最適化など import 以外の性能課題
- 既存言語仕様（演算意味、型規約）の変更
- 一度に全 backend を同一PRで完全移行すること

受け入れ基準:
- EAST 側で import 解決情報（`resolved_import` 相当）が参照可能である。
- CodeEmitter 基底が依存収集の単一 API を提供し、重複排除・安定順序で確定できる。
- 先行対象 backend（少なくとも Go）で固定 import とダミー未使用回避コードを撤去し、必要 import のみを出力できる。
- 回帰テストで「未使用 import を出さない」「必要 import は欠けない」を検知できる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go_smoke.py' -v`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2java_transpile.py`

決定ログ:
- 2026-02-28: ユーザー指示により、import 依存確定を「EAST 解決情報 + CodeEmitter 基底集約」で行う `P2` 計画を起票した。
- 2026-03-01: `meta.import_resolution`（`schema_version=1`）を導入し、`bindings` / `qualified_refs` を正本化した（既存 `import_bindings` / `qualified_symbol_refs` は互換維持）。
- 2026-03-01: `CodeEmitter.load_import_bindings_from_meta()` / `_resolve_imported_symbol()` は `import_resolution` を優先し、欠落時に legacy key へ fallback する fail-closed 方針へ更新した。
- 2026-03-01: parser からの記録値は欠落・不正値を解決対象へ昇格しない（空文字/欠落は解決不能として扱う）条件を固定し、既存挙動と互換にした。
- 2026-03-01: `CodeEmitter` 基底へ依存収集 API（`require_dep` / `require_dep_any` / `require_deps` / `finalize_deps`）を追加し、重複排除と安定順序化（既定ソート）を共通化した。
- 2026-03-01: Go native emitter を `CodeEmitter` 依存収集 API に接続し、`math` import を AST 走査で必要時のみ登録する方式へ移行した。
- 2026-03-01: Go 出力から `var _ = math.Pi` を撤去し、`sample/go` 再生成で残存ゼロを確認した。
- 2026-03-01: `test_py2go_smoke.py`（11件）を通過。`check_py2go_transpile.py` は既知の `Try/Yield/Swap` 4件 fail を維持（本タスク非対象）。
- 2026-03-01: import 回帰として `test_py2go_smoke.py` に「math未使用時は import なし」「math使用時のみ import あり」を固定し、`sample/go` 再生成と合わせて再発防止を CI 導線へ接続した。

## 分解

- [x] [ID: P2-EAST-IMPORT-RESOLUTION-01-S1-01] EAST3 で識別子/呼び出しの import 解決情報（module/symbol）を保持する仕様を定義する。
- [x] [ID: P2-EAST-IMPORT-RESOLUTION-01-S1-02] parser/lowering で解決情報を `meta` もしくはノード属性へ記録し、欠落時 fail-closed 条件を決める。
- [x] [ID: P2-EAST-IMPORT-RESOLUTION-01-S2-01] CodeEmitter 基底に `require_dep` / `finalize_deps` 等の依存収集 API を追加する。
- [x] [ID: P2-EAST-IMPORT-RESOLUTION-01-S2-02] backend 側で import 直書きを撤去し、基底の依存収集 API 経由へ段階移行する（先行: Go）。
- [x] [ID: P2-EAST-IMPORT-RESOLUTION-01-S2-03] 先行 backend（Go）で `var _ = math.Pi` など未使用回避ダミーを撤去し、必要 import のみ出力する。
- [x] [ID: P2-EAST-IMPORT-RESOLUTION-01-S3-01] import 回帰テスト（必要最小/未使用禁止/依存欠落禁止）を追加し、CI 導線へ固定する。

## S1 仕様（確定）

`Module.meta.import_resolution`（`schema_version=1`）:

- `schema_version: int`  
  現在は `1` 固定。
- `bindings: list[ImportBinding]`  
  parser/lowering が収集した import 束縛の正本。
- `qualified_refs: list[QualifiedSymbolRef]`  
  `from ... import ...` の解決済み参照（local 名を含む）。

`ImportBinding`:

- `module_id: str`（必須）
- `export_name: str`（`binding_kind="module"` の場合は空文字許容）
- `local_name: str`（必須）
- `binding_kind: "module" | "symbol"`（必須）
- `source_file: str`（任意）
- `source_line: int`（任意）

`QualifiedSymbolRef`:

- `module_id: str`（必須）
- `symbol: str`（必須）
- `local_name: str`（必須）

fail-closed ルール:

- `module_id` / `local_name` / `symbol` / `export_name` の必要値が空文字または欠落のエントリは、解決テーブルに登録しない。
- `import_resolution` がない、または `bindings` / `qualified_refs` が空の場合のみ、legacy キー（`import_bindings` / `qualified_symbol_refs` / `import_symbols` / `import_modules`）へ fallback する。
