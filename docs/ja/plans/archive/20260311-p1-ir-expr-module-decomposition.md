<a href="../../../en/plans/archive/20260311-p1-ir-expr-module-decomposition.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: `toolchain.ir` の大型 expr module を cluster 単位で分割する

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01`

背景:
- `P1-IR-CORE-DECOMPOSITION-01` と `P1-IR-ENTRYPOINT-FACADE-PRUNING-01` により、`src/toolchain/ir/core.py` は thin facade まで縮小した。
- ただし expr 系の split module にはまだ大型ファイルが残っている。現状は `core_expr_call_annotation.py` が 1000 行超、`core_expr_attr_subscript_suffix.py` が 600 行超で、責務境界が粗い。
- ここが大きいままだと、call/attr/subscript の小変更でも review 範囲が広くなり、source-contract test も「結局どの module を見ればよいか」が曖昧になる。

目的:
- `core.py` の次に重い expr split module を cluster 単位でさらに分割し、`attr suffix` / `subscript suffix` / `named-call` / `attr-call` / `callee-call` の責務境界を明確にする。
- source-contract test も split 後の module と 1:1 で追える構成へ寄せる。

対象:
- `src/toolchain/ir/core_expr_attr_subscript_suffix.py`
- `src/toolchain/ir/core_expr_call_annotation.py`
- `src/toolchain/ir/core_expr_shell.py`
- `tools/unittest/ir/_east_core_test_support.py`
- `tools/unittest/ir/test_east_core_source_contract_expr_suffix.py`
- `tools/unittest/ir/test_east_core_source_contract_call_dispatch.py`
- `tools/unittest/ir/test_east_core_source_contract_call_metadata.py`
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/p1-ir-expr-module-decomposition.md` / `docs/en/plans/p1-ir-expr-module-decomposition.md`

非対象:
- parser/IR/runtime 仕様変更
- nominal ADT / typed boundary の新規仕様追加
- backend 実装変更

受け入れ基準:
- `attr suffix` と `subscript suffix` が dedicated module に分かれる。
- `named-call` / `attr-call` / `callee-call` annotation cluster も bundle 単位で dedicated module に分かれる。
- `_ShExprParser` は split 後の mixin を import するだけの orchestration に寄る。
- source-contract test が split 後の module 構成へ追従し、代表 regression (`test_east_core*.py`, `test_prepare_selfhost_source.py`, `build_selfhost.py`) が通る。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check/check_transpiler_version_gate.py`
- `python3 tools/run/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

分解:
- [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S1-01] `core_expr_call_annotation.py` / `core_expr_attr_subscript_suffix.py` の残 cluster を棚卸しし、split boundary を `attr_suffix` / `subscript_suffix` / `named_call` / `attr_call` / `callee_call` / `shared_state` で固定する。
- [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S1-02] TODO / plan の進捗メモを bundle 単位へ圧縮する運用をこの task に固定する。
- [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S2-01] `attr suffix` / `subscript suffix` cluster を別 module へ分割し、`core_expr_shell.py` の import を追従させる。
- [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S2-02] `named-call` / `attr-call` / `callee-call` annotation cluster を bundle 単位で別 module へ分割する。
- [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S3-01] source-contract test を split 後の module 構成へ追従させ、representative regression を通す。
- [ ] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S4-01] docs / TODO / archive を更新し、完了後は archive へ移す。

決定ログ:
- 2026-03-11: 初版作成。着手時点の主要大型 file は `core_expr_call_annotation.py` と `core_expr_attr_subscript_suffix.py` で、`core.py` はすでに thin facade になっているため、次の分割対象は expr split module 自体と判断した。
- 2026-03-11: `core_expr_attr_subscript_suffix.py` は `attr_suffix` / `subscript_suffix` / `shared_postfix_orchestration` に分ける。shared 側に残すのは `_resolve_postfix_span_repr` と postfix dispatch だけに絞る。
- 2026-03-11: `core_expr_call_annotation.py` は `named_call` / `attr_call` / `callee_call` / `shared_state_orchestration` に分ける。shared 側は `call payload` 構築、generic return inference、optional payload coalesce、lookup facade を持つ。
- 2026-03-11: この task の進捗メモは bundle 単位の 1 行要約だけを TODO に残し、helper 単位の列挙は plan の決定ログか commit message に限定する。
- 2026-03-11: `S2-01` で `core_expr_attr_suffix.py` / `core_expr_subscript_suffix.py` を追加し、`core_expr_attr_subscript_suffix.py` は `_ShExprPostfixSuffixParserMixin` と backward-compatible facade だけを持つ構成へ縮めた。`core_expr_shell.py` は split 後 mixin を個別 import する。
- 2026-03-11: `S2-02` の最初の bundle として `callee-call` cluster を `core_expr_callee_call_annotation.py` へ分離した。`core_expr_call_annotation.py` は facade と shared call-state helper を持ち、callee-specific return inference / dispatch は dedicated mixin 側へ寄せる。
- 2026-03-11: `S2-02` は `core_expr_named_call_annotation.py` / `core_expr_attr_call_annotation.py` / `core_expr_callee_call_annotation.py` の 3 分割で完了とする。`core_expr_call_annotation.py` は `_build_call_expr_payload` と generic call orchestration を持つ facade まで縮んだ。
- 2026-03-11: `S3-01` では `_east_core_test_support.py` と `test_east_core_source_contract_*` 群を split 後 module layout へ追従させ、`test_east_core*.py` / `test_prepare_selfhost_source.py` / `build_selfhost.py` が通る状態を完了条件に固定した。
