# P1: `core.py` / `test_east_core.py` の分割と cluster 単位運用

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-IR-CORE-DECOMPOSITION-01`

背景:
- `src/toolchain/ir/core.py` は 10,081 行、`test/unit/ir/test_east_core.py` は 3,912 行あり、探索・レビュー・差分把握のコストが高い。
- `P2-COMPILER-TYPED-BOUNDARY-01-S3-02` では helper 抽出自体は進んだが、1 helper = 1 commit の粒度が細かすぎて、全体の前進量に対して commit 数と進捗メモが過剰になった。
- `test_east_core.py` には source-contract guard と parser behavior test が混在しており、分割の優先順位が見えにくい。

目的:
- `core.py` と `test_east_core.py` を責務ごとの module / test file へ分割し、cluster 単位で進められる構造にする。
- source-contract guard、parser behavior、suffix/call cluster の責務境界を明確化する。
- TODO / plan の進捗メモを cluster 単位に圧縮し、作業量に見合う粒度へ戻す。

対象:
- `src/toolchain/ir/core.py`
- `src/toolchain/ir/core_expr_*.py`
- `test/unit/ir/test_east_core.py`
- `test/unit/ir/test_east_core*.py`
- `docs/ja/todo/index.md`, `docs/en/todo/index.md`
- `docs/ja/plans/*.md`, `docs/en/plans/*.md`

非対象:
- IR 仕様変更
- nominal ADT / typed boundary 自体の新機能追加
- backend ごとの codegen 品質改善

受け入れ基準:
- `core.py` の責務が少なくとも `builder/core`, `suffix parser`, `call annotation` などの単位で読み分けやすくなる。
- `test_east_core.py` から source-contract guard と parser behavior が段階的に別ファイルへ分離される。
- 各 slice は 5-10 個程度の helper / test cluster をまとめて扱い、micro-commit に戻らない。
- TODO / plan の進捗メモは cluster 単位の要約に圧縮される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## 分解

- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S1-01] `core.py` / `test_east_core.py` の split boundary を棚卸しし、source-contract / parser behavior / suffix-call cluster の分割順を固定する。
- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S1-02] TODO / plan の進捗メモを cluster 単位へ圧縮する運用ルールをこの計画に反映する。
- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S2-01] `test_east_core.py` の先頭 source-contract builder cluster を shared support module と専用 test file へ切り出す。
- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S2-02] 残る source-contract guard を cluster ごとの `test_east_core_source_contract_*.py` へ分割する。
- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] parser behavior / diagnostics / nominal ADT representative tests を別 test file へ分割する。
- [ ] [ID: P1-IR-CORE-DECOMPOSITION-01-S3-01] `core.py` 側の残 cluster を bundle 単位で専用 module へ寄せる。
- [ ] [ID: P1-IR-CORE-DECOMPOSITION-01-S4-01] representative IR/selfhost regression を通し、分割後の運用メモを圧縮して安定化する。

決定ログ:
- 2026-03-11: `core.py=10081 lines`, `test_east_core.py=3912 lines` を基準に、本タスクを起票した。最初の slice は `test_east_core.py` の先頭 source-contract builder cluster を shared support module と専用 test file に切り出す方針とする。
- 2026-03-11: 以後の分割は「1 helper = 1 commit」ではなく、5-10 個の helper / test cluster をまとめた bundle で扱う。TODO / plan の進捗メモも bundle 単位の 1 行要約へ圧縮する。
- 2026-03-11: TODO には cluster 単位の一行進捗だけを残し、検証ログや判断理由は plan の `決定ログ` に集約する。以後の `S2` 以降もこの運用を維持する。
- 2026-03-11: `test/unit/ir/_east_core_test_support.py` と `test/unit/ir/test_east_core_source_contract_builders.py` を追加し、`test_east_core.py` 先頭の builder source-contract guard 10 本を専用 test file へ移した。
- 2026-03-11: `test/unit/ir/test_east_core_source_contract_expr_suffix.py` を追加し、call/attr/subscript の source-contract guard 10 本を `test_east_core.py` から切り出した。`S2-02` は残り source-contract cluster があるため継続する。
- 2026-03-11: `test/unit/ir/test_east_core_source_contract_call_metadata.py` を追加し、method/named-call metadata source-contract guard 10 本を `test_east_core.py` から切り出した。`S2-02` は残りの call suffix / parser helper / tuple-destructure cluster があるため継続する。
- 2026-03-11: `test/unit/ir/test_east_core_source_contract_runtime_builtins.py` と `test/unit/ir/test_east_core_source_contract_call_dispatch.py` を追加し、残りの runtime-builtin / named-call / call-suffix source-contract guard 19 本を `test_east_core.py` から切り出した。tuple-destructure と residual-inline-kind guard も既存 source-contract file へ吸収し、`test_east_core.py` は parser behavior / representative regression 中心へ整理した。
- 2026-03-11: `test/unit/ir/test_east_core_parser_behavior_decorators.py` を追加し、extern / abi / template の representative parser behavior 10 本を `test_east_core.py` から切り出して `S2-03` を開始した。
- 2026-03-11: `test/unit/ir/test_east_core_parser_behavior_types.py` を追加し、decode-first guard・type-expr・`typing` / `__future__` の representative parser behavior 10 本を `test_east_core.py` から切り出した。
- 2026-03-11: `test/unit/ir/test_east_core_parser_behavior_diagnostics.py` を追加し、object receiver diagnostics 3 本を `test_east_core.py` から切り出した。あわせて decorator / abi / template の負例 7 本も `test_east_core_parser_behavior_decorators.py` へ寄せ、`test_east_core.py` 先頭の重複 test と stray assert を除去した。
- 2026-03-11: `test/unit/ir/test_east_core_parser_behavior_exprs.py` を追加し、comprehension / lambda / fstring / yield / basic parser acceptance の representative 10 本を `test_east_core.py` から切り出した。
- 2026-03-11: `test/unit/ir/test_east_core_parser_behavior_classes.py` を追加し、class storage hint / dataclass / nominal ADT / enum の representative parser behavior 7 本を `test_east_core.py` から切り出した。
- 2026-03-11: `test/unit/ir/test_east_core_parser_behavior_runtime.py` を追加し、runtime annotation / builtin call / pathlib / json / iter lowering の representative parser behavior 12 本を `test_east_core.py` から切り出した。
- 2026-03-11: `test/unit/ir/test_east_core_parser_behavior_statements.py` を追加し、identifier/import ambiguity・`super()`・bare `return`・arg usage・trailing semicolon の representative parser behavior 6 本を `test_east_core.py` から切り出した。`test_east_core.py` には residual source-contract 3 本だけが残っている。
- 2026-03-11: `test_east_core.py` が residual source-contract 3 本だけになったため、`S2-03` は完了とする。次の束は `S3-01` として `core.py` 側の declaration / class-semantics cluster を module 単位で外へ出す。
- 2026-03-11: `core_class_semantics.py` を追加し、`_sh_make_decl_meta` / `_sh_make_nominal_adt_v1_meta` / dataclass value-safe 判定 / nominal ADT class metadata 収集を `core.py` から移した。`core.py` 側は decorator parser と class parse orchestration だけを維持する。
- 2026-03-11: `core_expr_attr_subscript_annotation.py` へ `_apply_attr_expr_annotation` / `_annotate_attr_expr` / `_annotate_subscript_expr` を移し、`test_east_core_source_contract_expr_suffix.py` を split 後の所在に合わせて更新した。`S3-01` は attr/subscript annotation cluster から着手した。
- 2026-03-11: `core_decorator_semantics.py` を追加し、`_sh_parse_decorator_head_and_args` / `_sh_is_dataclass_decorator` / `_sh_is_sealed_decorator` / `_sh_is_abi_decorator` / `_sh_is_template_decorator` を `core.py` から移した。decorator cluster は source-contract 専用 test で固定する。
- 2026-03-11: `core_extern_semantics.py` を追加し、`_sh_expr_attr_chain` / `_sh_is_extern_symbol_ref` / `_sh_collect_extern_var_metadata` を `core.py` から移した。ambient extern binding cluster は source-contract 専用 test で固定する。
- 2026-03-11: `core_runtime_decl_semantics.py` を追加し、`_sh_parse_runtime_abi_string_literal` / `_sh_parse_runtime_abi_mode` / `_sh_parse_runtime_abi_args_map` を `core.py` から移した。runtime ABI literal/mode cluster は callback injection を伴う source-contract test で固定する。
- 2026-03-11: `core_runtime_decl_semantics.py` へ `_sh_parse_runtime_abi_decorator` / `_sh_collect_runtime_abi_metadata` / `_sh_parse_template_decorator` / `_sh_collect_template_metadata` も移し、function parse site では callback injection 経由で collector だけを呼ぶ形に整理した。
- 2026-03-11: `core_runtime_decl_semantics.py` に `_sh_collect_function_runtime_decl_metadata` と class/method/top-level の runtime ABI/template misuse guard helper を追加し、`core.py` 側の残りを declaration parse orchestration に縮めた。
- 2026-03-11: `core_string_semantics.py` を追加し、`_sh_scan_string_token` / `_sh_decode_py_string_body` / `_sh_append_fstring_literal` を `core.py` から切り出した。f-string literal append は core へ逆依存しない薄い `Constant` node dict を返す。
- 2026-03-11: `core_text_semantics.py` を追加し、`_sh_is_identifier` / `_sh_strip_utf8_bom` / `_sh_is_dotted_identifier` / `_sh_split_top_keyword` / `_sh_split_top_level_as` / `_sh_parse_import_alias` / `_sh_parse_dataclass_decorator_options` を `core.py` から移した。import alias と dataclass option は callback injection つき source-contract で固定する。
- 2026-03-11: `core_string_semantics.py` を追加し、`_sh_scan_string_token` / `_sh_decode_py_string_body` / `_sh_append_fstring_literal` を `core.py` から移した。string token scan は `_make_east_build_error` / `_sh_span` を callback injection で受け取り、f-string literal append と合わせて source-contract で固定する。
- 2026-03-11: `core_stmt_text_semantics.py` を追加し、`_sh_split_top_level_assign` / `_sh_strip_inline_comment` / `_sh_raise_if_trailing_stmt_terminator` / `_sh_split_top_level_from` / `_sh_split_top_level_in` / `_sh_split_top_level_colon` / `_sh_parse_except_clause` / `_sh_parse_class_header_base_list` / `_sh_parse_class_header` を `core.py` から移した。statement/header text helper は `make_east_build_error` / `make_span` / `split_top_commas` を callback injection で受け取り、専用 source-contract test で固定する。
- 2026-03-11: `core_stmt_text_semantics.py` を logical-line merge / top-level split / comprehension target bind / indented-block collect まで拡張し、stmt-text helper の重複定義を `core.py` から除去した。source-contract は stmt-text helper の import/use/不在をまとめて検証する。
