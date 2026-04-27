# P0-FIXTURE-PARITY-161: fixture parity 161 件化の fail 調査

## 目的

fixture が 161 件へ増えたあと、C++ 以外の backend が 161/161 に揃っていない。`runtime_parity_check_fast.py --targets <lang> --case-root fixture` の結果を言語別に棚卸しし、実修正を各 backend TODO へ渡せる粒度へ分類する。

## 決定ログ

### 2026-04-27: S1/S2 fail リスト作成と分類

参照元:

- `docs/ja/progress-preview/backend-progress-fixture.md` 生成日時 `2026-04-27 11:48:20`
- `.parity-results/*_fixture.json` 既存蓄積結果
- spot check: `PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets rs,cs,ps1,js,ts,dart,go,java,scala,kotlin,swift,ruby,lua,php,nim,julia,zig --case-root fixture --cmd-timeout-sec 120`

全言語一括の fresh sweep は compile/run が重く、`bitwise_invert_basic` 実行中に中断した。`add` / `assign` の spot check では `java` の operator rendering regression と `zig` の `exception_style` profile mismatch が観測されたが、S1/S2 の正本リストは既存の 161 件マトリクスを採用する。

### 言語別 fail / 未実行リスト

| backend | pass | fail | 未実行 | 対象ケース |
|---|---:|---:|---:|---|
| rs | 151 | 7 | 3 | FAIL: `collections/reversed_basic`, `imports/import_math_module`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`, `typing/optional_none`, `typing/union_basic`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| cs | 135 | 23 | 3 | FAIL: `collections/iterable`, `collections/reversed_basic`, `collections/slice_basic`, `control/nested_closure_def`, `control/yield_generator_min`, `core/class_body_pass`, `core/class_tuple_assign`, `core/lambda_as_arg`, `core/lambda_basic`, `core/lambda_capture_multiargs`, `core/lambda_ifexp`, `core/lambda_local_state`, `core/obj_attr_space`, `core/pass_through_comment`, `imports/bom_from_import`, `imports/from_import_symbols`, `imports/from_pytra_std_import_math`, `imports/type_ignore_from_import`, `signature/ok_lambda_default`, `typing/callable_higher_order`, `typing/callable_optional_none`, `typing/int8`, `typing/tuple_unpack_variants`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| ps1 | 153 | 0 | 8 | 未実行: `collections/reversed_basic`, `collections/set_update`, `collections/sorted_set`, `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/isinstance_chain_narrowing`, `typing/isinstance_union_narrowing`, `typing/nullable_dict_field` |
| js | 151 | 7 | 3 | FAIL: `collections/dict_mutation_methods`, `collections/list_mutation_methods`, `collections/reversed_basic`, `collections/set_mutation_methods`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| ts | 150 | 8 | 3 | FAIL: `collections/dict_mutation_methods`, `collections/list_mutation_methods`, `collections/reversed_basic`, `collections/set_mutation_methods`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`, `typing/bytearray_basic`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| dart | 148 | 10 | 3 | FAIL: `collections/reversed_basic`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`, `strings/str_methods_extended`, `typing/int8`, `typing/integer_promotion`, `typing/isinstance_pod_exact`, `typing/str_repr_containers`, `typing/union_return_errorcheck`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| go | 154 | 4 | 3 | FAIL: `collections/reversed_basic`, `signature/ok_typed_varargs_representative`, `typing/isinstance_union_narrowing`, `typing/optional_none`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| java | 152 | 6 | 3 | FAIL: `collections/reversed_basic`, `control/exception_bare_reraise`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`, `typing/callable_optional_none`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| scala | 139 | 19 | 3 | FAIL: `collections/deque_basic`, `collections/reversed_basic`, `core/class_body_pass`, `imports/from_import_symbols`, `imports/from_pytra_std_import_math`, `imports/import_math_module`, `imports/type_ignore_from_import`, `oop/eo_extern_opaque_basic`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`, `strings/str_methods_extended`, `typing/callable_optional_none`, `typing/isinstance_chain_narrowing`, `typing/isinstance_narrowing`, `typing/isinstance_union_narrowing`, `typing/none_optional`, `typing/optional_none`, `typing/union_list_mixed`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| kotlin | 141 | 17 | 3 | FAIL: `collections/reversed_basic`, `core/class_body_pass`, `imports/from_import_symbols`, `imports/from_pytra_std_import_math`, `imports/import_math_module`, `imports/type_ignore_from_import`, `oop/eo_extern_opaque_basic`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`, `strings/str_methods_extended`, `typing/callable_optional_none`, `typing/isinstance_chain_narrowing`, `typing/isinstance_narrowing`, `typing/isinstance_union_narrowing`, `typing/none_optional`, `typing/optional_none`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| swift | 153 | 5 | 3 | FAIL: `collections/reversed_basic`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`, `typing/isinstance_union_narrowing`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| ruby | 155 | 3 | 3 | FAIL: `collections/reversed_basic`, `signature/ok_typed_varargs_representative`, `typing/callable_optional_none`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| lua | 157 | 1 | 3 | FAIL: `typing/bytes_copy_semantics`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| php | 154 | 4 | 3 | FAIL: `collections/reversed_basic`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| nim | 142 | 16 | 3 | FAIL: `collections/list_repeat`, `collections/nested_types`, `collections/reversed_basic`, `collections/sorted_basic`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`, `strings/str_methods_extended`, `typing/isinstance_chain_narrowing`, `typing/isinstance_union_narrowing`, `typing/object_container_access`, `typing/tuple_unpack_variants`, `typing/type_alias_pep695`, `typing/typed_container_access`, `typing/union_basic`, `typing/union_list_mixed`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| julia | 156 | 2 | 3 | FAIL: `collections/reversed_basic`, `signature/ok_typed_varargs_representative`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |
| zig | 150 | 8 | 3 | FAIL: `control/finally`, `signature/ok_typed_varargs_representative`, `typing/bytearray_basic`, `typing/callable_optional_none`, `typing/isinstance_narrowing`, `typing/isinstance_union_narrowing`, `typing/union_basic`, `typing/union_dict_items`; 未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` |

### 原因分類

| 分類 | 主なケース | 対象 backend | 対応方針 |
|---|---|---|---|
| 未実行 / 結果未蓄積 | `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field` | 全非 C++ backend | まず各 backend で単体実行して `.parity-results` を更新する。fail した場合は下記分類へ移す。 |
| 未実行 / backend 固有 | `collections/set_update`, `collections/sorted_set`, `typing/isinstance_chain_narrowing`, `typing/isinstance_union_narrowing` | ps1 | PowerShell backend 側で単体実行し、未対応なら emitter/runtime へ展開する。 |
| runtime 未実装・互換不足 | `collections/reversed_basic`, `collections/*_mutation_methods`, `collections/deque_basic`, `collections/list_repeat`, `collections/sorted_basic`, `strings/str_methods_extended`, `typing/bytes_copy_semantics`, `typing/bytearray_basic` | 多言語 | 各 runtime の collection/string/bytes helper を補完する。EAST3 側で追加意味を決める必要は現時点では低い。 |
| emitter 未対応 | `signature/ok_typed_varargs_representative`, `oop/trait_basic`, `oop/trait_with_inheritance`, `control/finally`, `control/exception_bare_reraise`, `control/yield_generator_min`, C# lambda/closure 系 | 多言語 | EAST3 の既存ノードを backend 表現へ落とす実装不足。emitter guide に従い、型推論を emitter に追加しない。 |
| import / module wiring | `imports/import_math_module`, `imports/from_import_symbols`, `imports/from_pytra_std_import_math`, `imports/type_ignore_from_import`, `imports/bom_from_import` | rs, cs, scala, kotlin | emit 出力の module path / symbol qualification / runtime copy の不整合を確認する。 |
| 型・narrowing・union runtime | `typing/optional_none`, `typing/none_optional`, `typing/callable_optional_none`, `typing/isinstance_*`, `typing/union_*`, `typing/type_alias_pep695`, `typing/typed_container_access`, `typing/object_container_access` | 多言語、特に JVM/Nim/Zig | type_id / optional / ADT runtime と emitter の接続不足。EAST3 前段バグに見える場合だけ `resolve/compile/optimize` へ戻す。 |
| 数値型・小整数 | `typing/int8`, `typing/integer_promotion`, `typing/isinstance_pod_exact` | cs, dart | target runtime の整数幅・promotion・POD 判定の互換不足を確認する。 |
| 実行環境・target profile 不整合 | spot check の `zig exception_style mismatch`, `java Add/Mult operator rendering` | zig, java | 161 件マトリクスとは別に要再確認。profile や renderer dispatch の regression であれば P0 修正対象に昇格する。 |

### S3 への引き継ぎ

S3 は「各 backend 担当が自分の言語を 161/161 に修正する」実装タスクとして残す。着手順は、全 backend 共通の未実行 3 件を先に確定し、次に多言語横断で重複している `reversed_basic` / `ok_typed_varargs_representative` / trait 2 件を優先する。
