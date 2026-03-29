<a href="../../en/plans/p3-codeemitter-cs-isolation.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P3: CodeEmitter から C# selfhost 起因修正を隔離

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P3-CODEEMITTER-CS-ISOLATION-01`

背景:
- C# selfhost 対応の過程で、`CodeEmitter`（共通基底）へ C# 固有事情に起因する調整が混入した。
- ユーザー方針として「C# 変換器未対応を理由に compiler 共通層を変更しない」を優先する。
- 共通層へ言語固有回避策が残ると、他 backend の回帰範囲と保守コストが増える。

目的:
- `CodeEmitter` の責務を「全 backend 共通ロジック」に再限定し、C# 固有回避は `CSharpEmitter` / C# runtime / selfhost 準備層へ移す。

対象:
- `src/pytra/compiler/east_parts/code_emitter.py`
- `src/hooks/cs/emitter/cs_emitter.py`
- 必要に応じて `tools/prepare_selfhost_source_cs.py` / `src/runtime/cs/*`
- 回帰確認: `tools/unittest/test_code_emitter.py` / `tools/unittest/test_py2cs_smoke.py` / `tools/check/check_multilang_selfhost_stage1.py` / `tools/check/check_multilang_selfhost_multistage.py`

非対象:
- C# backend の新機能追加（最適化や構文拡張）
- JS/TS/Go/Java/Swift/Kotlin 側の selfhost 改修
- EAST3 最適化層の新規仕様追加

受け入れ基準:
- `CodeEmitter` 変更のうち C# 固有理由のものが、根拠付きで「移管済み」または「共通必須」として分類される。
- C# 固有実装は `CSharpEmitter` など C# 側へ移管され、`CodeEmitter` は backend 中立な形へ戻る。
- `test_code_emitter` / `test_py2cs_smoke` が通過する。
- `check_multilang_selfhost_stage1.py` / `check_multilang_selfhost_multistage.py` で C# の `pass` を維持する。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_code_emitter.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`
- `python3 tools/check/check_multilang_selfhost_stage1.py`
- `python3 tools/check/check_multilang_selfhost_multistage.py`

分解:
- [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S1-01] `v0.4.0` 以降の `CodeEmitter` 差分を棚卸しし、「共通必須 / C# 固有 / 判定保留」の3分類を作成する。
- [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S1-02] 「共通必須」の判定基準（backend 中立性・他言語利用実績・fail-closed 必要性）を明文化する。
- [x] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-01] 「C# 固有」変更を `CSharpEmitter` / C# runtime / selfhost 準備層へ移管する。
- [x] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-02] `CodeEmitter` から C# 固有回避コードを除去し、共通実装へ戻す。
- [x] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S3-01] unit/selfhost 回帰を実施し、C# pass 維持と他 backend 非退行を確認する。

## S1-01 棚卸し（v0.4.0=96898f02 以降）

分類は `git log 96898f02..HEAD -- src/pytra/compiler/east_parts/code_emitter.py` を基準に作成した。

### 共通必須（維持候補）

1. `fe81e0a1`（依存収集API）  
   - `require_dep*` / `finalize_deps` は Go emitter で利用され、C# 固有ではない。
2. `72e3895a`（`import_resolution` 受理）  
   - 複数 backend が `load_import_bindings_from_meta` を共有し、IR 契約の後方互換維持に必要。
3. `11d50618`（ForCore downrange mode 解決）  
   - `cs/js/ts/rs/lua` が `resolve_forcore_static_range_mode` を利用。
4. `cc49329e`（`rc_new` 型復元補助）  
   - C++ 出力品質改善由来であり、C# selfhost 固有理由ではない。

### C# 固有（移管候補）

1. `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` 群（`6ff2dbe7`〜`f9e3a5b6`）  
   - `any_dict_get*` / `emit_with_scope` / hook 返り値処理の `Any` 化など、C# selfhost の object 型整合で導入された緩和。
2. `5d00eda8` / `a101d8d5` / `003424db`  
   - C# selfhost stage1/multistage の通過を主目的とする調整。

### 判定保留

1. ASCII 判定 helper 群（`_is_ascii_*`）  
   - 実装意図は C# selfhost 起点だが、識別子/フック名正規化の共通安定化にも寄与しうる。
2. `any_to_dict_or_empty` の key 正規化コピー  
   - C# object-safe 化由来だが、非文字列 key 混入時の fail-closed 強化として共通採用余地あり。

## S1-02 判定基準（共通必須）

「共通必須」と判定する条件を次の3軸で固定する。

1. backend 中立性  
   - API/挙動が特定言語固有型（例: C# の `object` 都合）を前提にしない。
2. 他言語利用実績  
   - C# 以外の emitter が実際に呼び出している、または IR 契約上必須である。
3. fail-closed 必要性  
   - 取り除くと未解決 import・range mode 破綻などの安全性低下を招く。

上記 3 条件のいずれかを満たさない変更は、原則として C# 側へ移管候補に分類する。

決定ログ:
- 2026-03-01: ユーザー指示により「CodeEmitter へ C# 都合を持ち込まない」方針を明示し、実装着手前に P3 計画化することを決定した。
- 2026-03-02: S1-01 として `v0.4.0` 以降の `CodeEmitter` 差分を commit 単位で棚卸しし、共通必須 / C# 固有 / 判定保留の3分類を作成した。
- 2026-03-02: S1-02 として共通必須の判定基準（backend中立性・他言語利用実績・fail-closed必要性）を明文化した。
- 2026-03-02: S2-01 として scope 名正規化（`_normalize_scope_names`）を `CodeEmitter` から `CSharpEmitter` へ移管し、共通層は `set[str]` 前提へ戻した。`test_code_emitter` / `test_py2cs_smoke` は通過、`check_py2cs_transpile` の fail 2件（`yield_generator_min.py`/`tuple_assign.py`）は既知継続。
- 2026-03-02: S2-02 として `is_declared` の逆順走査を C# 回避 `while` から共通実装 `range(...,-1,-1)` へ戻し、`_const_int_literal` の返り型注釈を `int|None` へ復帰。unit/smoke は通過し、`check_py2cs_transpile` fail 2件は既知継続。
- 2026-03-02: S3-01 として `test_code_emitter` / `test_py2cs_smoke` / `check_multilang_selfhost_stage1 --strict-stage1` / `check_multilang_selfhost_multistage` を再実行。C# は stage1/native・multistage(stage1/2/3) とも `pass` を回復。併せて `transpile_cli` helper 抽出リスト（`prepare_selfhost_source.py`）と C# selfhost compile blocker（typed container/keyword引数/dict key型）を整理した。
