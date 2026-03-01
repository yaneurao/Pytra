# P1: EAST2 を最初の共通 IR として再定義（Python 依存排除）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-EAST2-COMMON-IR-01`

背景:
- 現状の EAST2/EAST2->EAST3 連携には、`py_*` 命名や Python builtin 名前提の契約が残っており、IR 境界として Python 依存が混入している。
- 将来的に複数フロントエンド（Python 以外）を受ける場合、最初の共通 IR は言語非依存である必要がある。
- EAST2 が中立でないと、backend 側へ source 言語依存が漏れ、最適化・検証・保守が難しくなる。

目的:
- EAST2 を「source 言語非依存の最初の共通 IR」として定義し直す。
- Python 固有仕様（builtin 解決、標準ライブラリ慣習、補助 runtime 名称）を frontend 境界へ隔離する。
- EAST2->EAST3 lowering は中立契約の消費者に限定する。

対象:
- `src/pytra/compiler/east_parts/east2.py`
- `src/pytra/compiler/east_parts/east2_to_east3_lowering.py`
- `src/pytra/compiler/east_parts/core.py`（frontend 境界の調整範囲）
- `docs/ja/spec/spec-east.md`（必要に応じて関連仕様追記）
- EAST2/EAST3 周辺の unit test

非対象:
- Ruby/Lua/PHP など新規 frontend 実装の同時着手
- EAST3 optimizer 全面改修
- 各 backend emitter の大規模最適化

受け入れ基準:
- EAST2 契約（ノード・メタ・lowering 入力条件）から Python 固有名称依存が除去される。
- Python 固有解決ロジックは frontend 側 adapter に局所化される。
- EAST2->EAST3 lowering が中立契約のみを参照して動作する。
- 既存 Python 入力の transpile/smoke が非退行で通過する。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test_east*.py' -v`
- `python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

決定ログ:
- 2026-03-01: ユーザー指示により、「EAST2 を最初の共通 IR として運用するための Python 依存排除」を P1 で分割着手する方針を確定した。
- 2026-03-01: `S1-01` として `core.py` / `east2_to_east3_lowering.py` の Python 依存契約（`py_*` runtime call、builtin 名直参照、`py_tid_*` 互換分岐）を棚卸しし、S2 実装入力を固定した。
- 2026-03-01: `docs/ja/spec/spec-east.md` に「EAST2 共通 IR 契約（Depythonization Draft）」を追記し、ノード種別/演算子/メタ/診断/fail-closed 条件を明文化した。
- 2026-03-01: `src/pytra/compiler/stdlib/frontend_semantics.py` を追加し、Python builtin/std の semantic tag 解決を frontend adapter へ分離した。
- 2026-03-01: `core.py` は `semantic_tag` 付与を adapter 経由へ切り替え、`east2_to_east3_lowering.py` は `semantic_tag` 優先で Obj* / type predicate lower するよう更新した（`runtime_call` は互換保持）。
- 2026-03-01: 回帰として `test_stdlib_signature_registry.py`, `test_east_core.py`, `test_east2_to_east3_lowering.py` の semantic-tag 系テストを追加/更新し、該当テスト pass を確認した。
- 2026-03-01: `core.py` の `isinstance/issubclass` を `lowered_kind=TypePredicateCall + builtin_name` で中立表現化し、`east2_to_east3_lowering.py` は `semantic_tag` / `TypePredicateCall` 優先で type predicate を lower するよう更新した（関数名直参照は legacy fallback へ縮退）。
- 2026-03-01: `meta.legacy_compat_bridge`（既定 `true`）を `east2_to_east3_lowering.py` へ導入し、legacy name/builtin fallback を段階的に停止可能な互換ブリッジを明示化した。
- 2026-03-01: 回帰として `legacy_compat_bridge=false` 時に legacy fallback が無効化されるテスト（builtin/type-predicate）を追加し、既存 semantic-tag 経路と両立することを確認した。

## 分解

- [x] [ID: P1-EAST2-COMMON-IR-01-S1-01] EAST2/EAST2->EAST3 に残る Python 依存契約（`py_*` runtime call、builtin 名直参照、型メタ前提）を棚卸しする。
- [x] [ID: P1-EAST2-COMMON-IR-01-S1-02] EAST2 共通 IR 契約（ノード種別、演算子、メタ情報、診断と fail-closed 条件）を仕様化する。
- [x] [ID: P1-EAST2-COMMON-IR-01-S2-01] Python 固有の builtins/std 解決を frontend adapter 層へ移管し、EAST2 契約から分離する。
- [x] [ID: P1-EAST2-COMMON-IR-01-S2-02] `east2_to_east3_lowering.py` を中立契約ベースへ更新し、Python 名称分岐を縮小・除去する。
- [x] [ID: P1-EAST2-COMMON-IR-01-S2-03] 既存入力非退行のための移行ブリッジ（暫定互換）を導入し、段階移行できる状態にする。
- [ ] [ID: P1-EAST2-COMMON-IR-01-S3-01] EAST2 への Python 依存再混入を検知する unit 回帰を追加する。
- [ ] [ID: P1-EAST2-COMMON-IR-01-S3-02] transpile/smoke/parity 代表ケースで非退行を確認し、決定ログへ記録する。

## S1-01 棚卸し結果（2026-03-01）

### `core.py`（frontend 境界）

- `src/pytra/compiler/east_parts/core.py:2455-2637`
  - `print/len/range/str/int/float/bool/min/max/open/iter/next/reversed/enumerate/any/all/ord/chr/list/set/dict/bytes/bytearray` を `BuiltinCall + runtime_call` へ直接 lower。
  - `runtime_call` が `py_*`（例: `py_len`, `py_to_string`, `py_iter_or_raise`）へ固定され、Python 組み込み識別子に強く依存。
- `src/pytra/compiler/east_parts/core.py:2528-2533,2642-2646`
  - `lookup_stdlib_*` により stdlib 関数/メソッドを runtime 名へ直接解決（frontend で言語固有契約を保持）。
- `src/pytra/compiler/east_parts/core.py:3674-3700`
  - `any/all(generator)` 正規化で `runtime_call=py_any/py_all` を直出し。
- `src/pytra/compiler/east_parts/core.py:2940`
  - `Path` を直接型名として扱う分岐が残存（`Path` 固有契約の混入）。

### `east2_to_east3_lowering.py`（EAST2->EAST3）

- `src/pytra/compiler/east_parts/east2_to_east3_lowering.py:142-151`
  - `_builtin_type_id_symbol` が `None/bool/int/float/str/list/dict/set/object` を固定テーブルで解決。
- `src/pytra/compiler/east_parts/east2_to_east3_lowering.py:351-368`
  - `isinstance/issubclass` と `py_isinstance/py_tid_*` 系を関数名直参照で分岐。
- `src/pytra/compiler/east_parts/east2_to_east3_lowering.py:620-657`
  - `runtime_call` 文字列（`py_to_bool`, `py_len`, `py_to_string`, `py_iter_or_raise`, `py_next_or_stop`）に依存して Obj* 境界ノードへ lower。
- `src/pytra/compiler/east_parts/east2_to_east3_lowering.py:664-687`
  - `builtin_name`（`bool/len/str`）の stage2 互換フォールバックが残存。
- `src/pytra/compiler/east_parts/east2_to_east3_lowering.py:692-708`
  - `iter/next` を関数名直参照で Obj* 境界へ lower。

### `east2.py`

- `src/pytra/compiler/east_parts/east2.py` は stage 正規化のみで Python 固有契約は確認されず。

### S2 への入力（優先順）

1. `core.py` の `builtin_name/runtime_call` 直書き分岐を frontend adapter 化し、EAST2 には中立 opcode/semantic tag のみ渡す。
2. `east2_to_east3_lowering.py` の `py_*` / `builtin_name` フォールバックを段階撤去し、中立タグ解釈へ置換する。
3. `isinstance/issubclass` など名前直参照分岐を「型述語ノード契約」に寄せ、関数名依存を境界外へ隔離する。
