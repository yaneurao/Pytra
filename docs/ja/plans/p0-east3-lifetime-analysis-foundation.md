<a href="../../en/plans/p0-east3-lifetime-analysis-foundation.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: EAST3 変数 lifetime 解析基盤の導入（backend 共通）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-EAST3-LIFETIME-ANALYSIS-01`

背景:
- 既存の EAST3 最適化には関数間 non-escape summary があるが、変数単位の live-range / last-use 情報は保持していない。
- そのため C++ では `object` / `rc` 縮退の根拠が emitter 側へ偏り、Rust 含む他 backend へ同じ最適化方針を横展開しづらい。
- backend ごとに lifetime 判定ロジックを持つと責務境界が崩れ、出力品質改善のたびに重複改修が発生する。

目的:
- EAST3 側で backend 非依存の lifetime 注釈（定義点・使用点・last-use・live-range）を生成する。
- 既存 non-escape 解析と接続し、`escape する値は保守側`、`non-escape で局所完結する値は最適化候補` を機械的に判定できる土台を作る。
- C++/Rust など各 emitter はこの注釈を「利用するだけ」に寄せる。

対象:
- `src/pytra/compiler/east_parts/east3_optimizer.py`
- `src/pytra/compiler/east_parts/east3_opt_passes/*`（新規 lifetime pass 群を追加）
- `src/pytra/compiler/east_parts/east3_opt_passes/non_escape_interprocedural_pass.py`（必要な接続のみ）
- `tools/unittest/test_east3_optimizer*.py`
- `tools/unittest/test_east3_lifetime_*.py`（新規）
- 必要最小限の `spec-east3-optimizer` 追記

非対象:
- C++/Rust emitter での実際の置換実装（`rc -> value`、borrow/move 化）
- alias/points-to の高精度化（本計画は fail-closed の実用最小）
- runtime 仕様変更

受け入れ基準:
- EAST3 pass 実行後、ローカル変数ごとに `live-range` と `last-use` 注釈が決定的に得られる。
- 分岐・ループ・tuple unpack・関数呼び出しを含むケースで解析結果が保守側に崩れず、再実行で同一結果になる。
- unresolved call / dynamic call を含む場合は fail-closed で lifetime 最適化候補から除外される。
- 既存 optimizer 回帰と transpile smoke（`py2cpp`/`py2rs`）が非退行で通る。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_lifetime_*.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer*.py' -v`
- `python3 tools/check/check_py2cpp_transpile.py`
- `python3 tools/check/check_py2rs_transpile.py`

決定ログ:
- 2026-03-02: ユーザー指示により、backend 側個別最適化より先に EAST3 で変数 lifetime 解析を共通化する方針を P0 で確定。
- 2026-03-02: [ID: `P0-EAST3-LIFETIME-ANALYSIS-01-S1-01`] `docs/ja/spec/spec-east3-optimizer.md` に `east3_lifetime_v1` 契約（`cfg/def_use/variables` と `fail_closed` 規則）を追記し、lifetime 注釈スキーマを固定した。
- 2026-03-02: [ID: `P0-EAST3-LIFETIME-ANALYSIS-01-S1-02`] `LifetimeAnalysisPass` を追加し、`FunctionDef/ClassDef method` 単位で block-local CFG と def-use index を生成して `meta.lifetime_analysis` へ注釈する基盤を実装した。
- 2026-03-02: [ID: `P0-EAST3-LIFETIME-ANALYSIS-01-S2-01`] 同 pass に backward data-flow（`live_in/live_out` 固定点）を実装し、分岐・ループを含む CFG で決定的に収束することを確認した。
- 2026-03-02: [ID: `P0-EAST3-LIFETIME-ANALYSIS-01-S2-02`] 文ノード `meta` へ `lifetime_node_id/defs/uses/live_in/live_out/last_use_vars` を注釈し、変数 summary（`last_use_nodes` 含む）を出力するようにした。
- 2026-03-02: [ID: `P0-EAST3-LIFETIME-ANALYSIS-01-S2-03`] `escape_summary.arg_escape` と `Return/Yield` 使用を lifetime class 判定に統合し、`escape_or_unknown` と `local_non_escape_candidate` を自動分類する実装を追加した。
- 2026-03-02: [ID: `P0-EAST3-LIFETIME-ANALYSIS-01-S3-01`] `test_east3_lifetime_analysis_pass.py` を新規追加し、分岐・ループ・tuple unpack・call（dynamic含む）・決定性・non_escape連携の回帰を固定した。
- 2026-03-02: [ID: `P0-EAST3-LIFETIME-ANALYSIS-01-S3-02`] `test_east3_optimizer*.py` / `test_east3_lifetime_analysis_pass.py` / `check_py2cpp_transpile.py` / `check_py2rs_transpile.py` を再実行し、非退行（`py2cpp: checked=136 ok=136 fail=0`, `py2rs: checked=131 ok=131 fail=0`）を確認した。

## 分解

- [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S1-01] lifetime 注釈スキーマ（`def/use`, `live_in/live_out`, `last_use`, `lifetime_class`）と fail-closed 規則を仕様化する。
- [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S1-02] EAST3 の関数/メソッド本体から block-local CFG と def-use index を生成する基盤を追加する。
- [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S2-01] backward data-flow で liveness（`live_in/live_out`）を求め、ループを含む固定点収束を実装する。
- [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S2-02] 使用列から last-use 点を確定し、ノード `meta` へ `last_use` / `live_range` を注釈する。
- [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S2-03] non-escape summary と結合し、`escape` 値を lifetime 最適化候補から除外する統合判定を実装する。
- [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S3-01] 分岐/ループ/tuple unpack/call を含む unit テストを追加し、決定性と fail-closed を固定する。
- [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S3-02] optimizer 回帰 + `check_py2cpp_transpile`/`check_py2rs_transpile` を実行し、非退行を確認する。
