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
- 回帰確認: `test/unit/test_code_emitter.py` / `test/unit/test_py2cs_smoke.py` / `tools/check_multilang_selfhost_stage1.py` / `tools/check_multilang_selfhost_multistage.py`

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
- `python3 tools/check_multilang_selfhost_stage1.py`
- `python3 tools/check_multilang_selfhost_multistage.py`

分解:
- [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S1-01] `v0.4.0` 以降の `CodeEmitter` 差分を棚卸しし、「共通必須 / C# 固有 / 判定保留」の3分類を作成する。
- [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S1-02] 「共通必須」の判定基準（backend 中立性・他言語利用実績・fail-closed 必要性）を明文化する。
- [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-01] 「C# 固有」変更を `CSharpEmitter` / C# runtime / selfhost 準備層へ移管する。
- [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-02] `CodeEmitter` から C# 固有回避コードを除去し、共通実装へ戻す。
- [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S3-01] unit/selfhost 回帰を実施し、C# pass 維持と他 backend 非退行を確認する。

決定ログ:
- 2026-03-01: ユーザー指示により「CodeEmitter へ C# 都合を持ち込まない」方針を明示し、実装着手前に P3 計画化することを決定した。
