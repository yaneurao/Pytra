# P1: C++ Emitter Reduction Plan

## 目的
`py2cpp.py` への責務集中を解消し、`CppEmitter` を中心に肥大化した変換ロジックを段階分解する。

C++ CodeEmitter の体積増加は「責務混入」と「経路の重複」が主因であり、原因を分けないまま一括改修すると再発しやすい。まずは下記 4 区分に明文化し、各区分を小粒度で切り出す。

## 背景
- `py2cpp.py` は CLI / I/O / オーケストレーションを担うレイヤであり、言語変換本体は保持しない構成へ収束している。
- 既に一部移管・再構成は進んでいるが、下位ロジックの「種類別」分離が未完のため、変更衝突と可読性劣化が継続している。
- 計測と品質検証（`sample` 再生成）と同時に進めないと、可読性改善が機能回帰を生みやすい。

## 方針
1. C++ CodeEmitter を「責務ごと」に分割する。
2. 1タスクあたり 1~2 点の責務を移譲する。
3. 各完了タスクに `test/unit` の回帰 + 変換回帰を紐づける。
4. `C++ 固有の最適化` と `共通化可能なロジック` を明確に分ける。
5. いったん `P0` が高リスク箇所を先に潰す。

## 分解カテゴリ

### 1) 責務境界再整理 (最優先)
- 目的: `CppEmitter` のメソッドをカテゴリ別モジュールへ段階移譲し、`src/hooks/cpp/emitter/` に構造を寄せる。
- 主な対象領域:
  - expression rendering
  - statement rendering
  - cast / runtime-call / import
  - control-flow helper
  - literal / trivia 補助

### 2) 既存責務の二重化・重複ロジック解消
- 目的: 同一目的で異なる実装を複数箇所で持つ箇所を一本化。
- 例: C++ と共通 CodeEmitter で同等のルールを別実装している箇所、型判定ヘルパ重複。

### 3) hooks / dispatch 化の最適化
- 目的: `emit_stmt` / `render_expr` 系の分岐を整理し、kind 固定ルート化を推進。
- 依存: `docs-ja/plans/p1-codeemitter-dispatch-redesign.md`

### 4) C++ 固有の最終調整フェーズ
- 目的: 量産生成物品質（`sample/cpp`）への影響を最小化しつつ、冗長出力の縮退を行う。
- 例: 既知の冗長パターンの段階的除去、`mut` / 括弧 / cast / import の扱い最適化
- 依存: `docs-ja/plans/p1-multilang-output-quality.md`

## 着手順（MVS）
- P0: 責務境界の再整理で「依存循環・副作用」を先に潰す。
- P1: 重複ロジック解消。
- P2: dispatch と hooks の最小化。
- P3: 出力品質調整。

## サブタスク例（粒度）
- 例: `CppEmitter` から statement 系ヘルパの抽出を 3〜5 関数ずつに分割。
- 例: `cast` パス内の runtime 呼び出し分岐を helper へ統合し、同機能の east 側移管可能性を明示。
- 例: `for`/`while` 由来の一時変数生成と破棄ロジックを専用モジュールに移譲。
- 例: `render_expr` の kind 分岐を `on_render_expr_*` 経路と整合。

## 受け入れ条件
- `py2cpp.py` で emitter 本体ロジックが増えない（責務移譲のみ）。
- 対応関数の移譲後、既存の公開 API は互換。
- `python3 test/unit/test_code_emitter.py`、
  `python3 test/unit/test_py2cpp_smoke.py`（既存ケース）、
  `python3 tools/check_py2cpp_transpile.py` が pass。
- `tools/run_local_ci.py` で C++ 変換関連ジョブの既存基線回帰なし。

## 関連文書
- `docs-ja/plans/p1-codeemitter-dispatch-redesign.md`
- `docs-ja/plans/p1-codeemitter-hooks-migration.md`
- `docs-ja/plans/p1-py2cpp-reduction.md`
- `docs-ja/plans/p1-py2cpp-reduction.md`
- `docs-ja/plans/p1-multilang-output-quality.md`
- `docs/spec/spec-dev.md`

## 備考
- 最終的な実施タスクは `docs-ja/todo/index.md` の当該IDへ登録し、各サブタスクは 1〜3 スモールコミット単位で進める。

## 決定ログ

- [2026-02-25] [ID: P1-CPP-EMIT-01-S1]
  - 実施内容: `src/hooks/cpp/emitter/expr.py` を新規作成し、`CppEmitter` の式系ヘルパ（`apply_cast` / `render_to_string` / `render_expr_as_any` / `render_boolop` / `render_cond` / `_str_index_char_access` / `render_minmax`）を `CppExpressionEmitter` へ移譲。
  - 呼び出し変更: `src/hooks/cpp/emitter/cpp_emitter.py` の `CppEmitter` を `CppExpressionEmitter, CodeEmitter` の多重継承に変更し、対象メソッドを削除して委譲先に移した。
  - 補足: `_try_optimize_char_compare` / `_byte_from_str_expr` は `cpp_char_lit` 依存のため、次サブタスクで移譲判断。

- [2026-02-25] [ID: P1-CPP-EMIT-01-S2]
  - 実施内容: `src/hooks/cpp/emitter/stmt.py` を新規編集し、`CppEmitter` の statement 系（`If` / `While` / `Try` / `For`）ヘルパを `CppStatementEmitter` へ移譲。
  - 呼び出し変更: `CppEmitter` を `CppStatementEmitter, CppExpressionEmitter, CodeEmitter` へ拡張し、移譲対象メソッドを `src/hooks/cpp/emitter/cpp_emitter.py` から除去。
  - 補足: `for` 系は既存動作を維持するため、`_emit_for_body_*`、`emit_for_range`、`emit_for_each`、runtime iterable 出力系を一括で移譲。

- [2026-02-25] [ID: P1-CPP-EMIT-01-S3]
  - 実施内容: `src/hooks/cpp/emitter/call.py` を新規作成し、`cast / runtime-call / import` の責務を `CppCallEmitter` に分離（`_lookup_module_attr_runtime_call`, `_resolve_runtime_call_for_imported_symbol`, `_resolve_or_render_imported_symbol_name_call`, `_render_builtin_static_cast_call`）。
  - 呼び出し変更: `CppEmitter` を `CppCallEmitter` を含む多重継承へ更新し、上記メソッドを `cpp_emitter.py` から除去。
  - 補足: cast/呼び出し分岐の重複参照箇所を整理し、後続で RuntimeCall 系分岐の追加拡張を集中可能にした。

- [2026-02-25] [ID: P1-CPP-EMIT-01-S4]
  - 実施内容: `src/hooks/cpp/emitter/tmp.py` を新規追加し、`CppEmitter` 共通の一時変数名生成責務を `CppTemporaryEmitter` へ集約。
  - 集約対象: `__finally`, `__it`, `__itobj`, `__tuple`, `__yield_values` の命名をヘルパ経由に統一し、`stmt.py` / `cpp_emitter.py` の直接 `next_tmp` 呼び出しを削減。
  - 補足: 一時変数の `scope` での生存域セットを明示的に再利用する `scope_names_with_tmp` を追加し、for 直下の scope 設定で利用する基盤を導入。

- [2026-02-25] [ID: P1-CPP-EMIT-01-S5]
  - 実施内容: `CodeEmitter` に `fallback_tuple_target_names_from_stmt(...)` を追加し、`target.repr` と `stmt.repr` 両対応のフォールバック復元を共通化。
  - 補足: C++ 側の `emit_assign` からインライン復元ロジックを除去し、共通 API を呼び出すだけに変更。`fallback_tuple_target_names_from_repr` 本体はそのまま維持し互換性を保つ。

- [2026-02-25] [ID: P1-CPP-EMIT-01-S6]
  - 実施内容: `CppEmitter` の `cast`/`object receiver` 周辺ロジックを `src/hooks/cpp/emitter/operator.py` の `CppBinaryOperatorEmitter` に切り分け。
  - 分離内容: `_render_binop_expr` / `_render_binop_dunder_call` / `_render_binop_operator` を再整理し、`expr` 表層整形、`dunder` 呼び出し、`op` 分岐の責務を 1 ハンドラ群に集約。
  - 補足: `cpp_emitter.py` は新規ヘルパーモジュールを継承する構成へ変更し、`BIN_OPS` の責務移譲先を明確化。

- [2026-02-25] [ID: P1-CPP-EMIT-01-S7]
  - 実施内容: `render_trivia` の責務を `src/hooks/cpp/emitter/trivia.py` の `CppTriviaEmitter` へ切り出し。
  - 実装内容: `CppEmitter` から trivia/コメント/ディレクティブ周辺の `emit_leading_comments` 実装を移譲し、`render_trivia` を経由して呼び出すように統一。
  - 補足: `emit_leading_comments` 本体は `CppTriviaEmitter` 側で再実装し、self-hosted 時の directive only 処理を維持。

- [2026-02-25] [ID: P1-CPP-EMIT-01-S8]
  - 実施内容: `py2cpp.py` の `_transpile_to_cpp_with_map` から `CppEmitter` 直呼び出しを排除し、`hooks.cpp.emitter.emit_cpp_from_east` への委譲へ変更。
  - 実装内容: `src/hooks/cpp/emitter/cpp_emitter.py` に `emit_cpp_from_east(...)` を追加し、`src/hooks/cpp/emitter/__init__.py` で公開。
  - 補足: `py2cpp.py` 側は CLI 引数整備と配線・再エクスポートに寄せ、`CppEmitter` の生成ロジックを直接持たないようにした。

- [2026-02-25] [ID: P1-CPP-EMIT-01-S9]
  - 実施内容: `check_py2cpp_transpile` / `test_py2cpp_smoke` を最新コードで通し、回帰結果を検証完了として確定。
  - 実行結果: `checked=150 ok=150 fail=0 skipped=6` / `Ran 3 tests in 1.298s`（`OK`）。
  - 補足: `PY2CPP` は self-host 連携を崩さない形で `CppEmitter` 実体委譲の前提（`from hooks.cpp.emitter import CppEmitter`）を維持。
