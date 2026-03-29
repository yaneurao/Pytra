<a href="../../../en/plans/archive/20260311-p0-starred-call-tuple-unpack-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: fixed tuple の starred call unpack を全言語で通す

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-STARRED-CALL-TUPLE-UNPACK-01`

背景:
- 現在の self-hosted parser は call argument 位置の `*expr` を読めず、`f(*t)` のような call unpack が `unsupported_syntax: self_hosted parser cannot parse expression token: *` で落ちる。
- Pytra-NES のような実験コードでは `t: tuple[int, int, int]` を `f(*t)` で渡す representative case が必要で、ここが止まると多言語 smoke まで進めない。
- repo 内では `Starred` を受ける analysis lane は一部存在するが、parser / lowering / backend smoke の contract はまだ閉じていない。

目的:
- representative v1 として `typed fixed tuple` に対する call unpack を self-hosted parser から全言語 backend まで通す。
- backend ごとの独自 special case を増やさず、EAST2->EAST3 lowering で positional arg へ正規化して共有 contract にする。

対象:
- call argument 位置の `*expr` parser / AST builder
- `Starred(value=t)` where `t: tuple[...]` の EAST2->EAST3 lowering
- `t: tuple[int, int, int]; f(*t)` representative fixture / parser regression / lowering regression
- all-target smoke と C++ runtime regression
- ja/en TODO / plan / docs の同期

非対象:
- list / dict / set literal の starred unpack
- assignment target の `a, *rest = xs`
- `**kwargs` unpack
- 動的長 tuple や `Any/object` receiver の starred unpack

受け入れ基準:
- self-hosted parser が `f(*t)` を受理し、call arg lane に `Starred` node を保持できること。
- `t: tuple[int, int, int]` の representative case で、EAST2->EAST3 lowering が positional arg 3 個へ正規化すること。
- representative fixture が C++ runtime で実行成功し、主要 backend smoke が通ること。
- unsupported lane（非 tuple / dynamic tuple / `**kwargs`）は silent fallback せず fail-closed を維持すること。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core_parser_behavior_exprs.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east2_to_east3_lowering.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/backends -p 'test_py2*_smoke.py' -k starred_call_tuple`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k starred_call_tuple`
- `python3 tools/build_selfhost.py`
- `python3 tools/check/check_transpiler_version_gate.py`
- `python3 tools/run/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

決定ログ:
- 2026-03-11: v1 は `typed fixed tuple` の call unpack に限定する。parser は `Starred` node を保持し、backend special case ではなく EAST2->EAST3 lowering で positional arg 展開する。
- 2026-03-11: representative smoke は `transpile success + raw "*receiver" leak 不在` を canonical contract にし、空ファイルを返す backend lane では source text 非空を必須にしない。
- 2026-03-11: representative regression で露出した `_const_int_node` import 漏れを修正し、parser / lowering / all-target transpile / C++ runtime まで通した状態で archive へ移す。

## 分解

- [x] [ID: P0-STARRED-CALL-TUPLE-UNPACK-01-S1-01] `Starred` の parser/AST contract、representative fixture、unsupported lane を plan/TODO に固定する。
- [x] [ID: P0-STARRED-CALL-TUPLE-UNPACK-01-S2-01] self-hosted parser と AST builder に call-arg `Starred` support を追加し、parser behavior test を通す。
- [x] [ID: P0-STARRED-CALL-TUPLE-UNPACK-01-S2-02] EAST2->EAST3 lowering で fixed tuple starred arg を positional arg 展開し、representative lowering regression を追加する。
- [x] [ID: P0-STARRED-CALL-TUPLE-UNPACK-01-S3-01] representative fixture と all-target smoke / C++ runtime regression、docs を更新して閉じる。
