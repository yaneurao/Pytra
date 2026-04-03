<a href="../../en/todo/julia.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Julia backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-03

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/julia/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/julia/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の Julia emitter: `src/toolchain/emit/julia/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の Julia runtime: `src/runtime/julia/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P1-JULIA-EMITTER: Julia emitter を toolchain2 に新規実装する

1. [ ] [ID: P1-JULIA-EMITTER-S1] `src/toolchain2/emit/julia/` に Julia emitter を新規実装する — CommonRenderer + override 構成。旧 `src/toolchain/emit/julia/` と TS emitter を参考にする
   - 2026-04-02: toolchain2 側に Julia emitter / CLI / profile を追加し、`pytra-cli.py emit --target julia` を toolchain2 経路へ接続。現状は旧 emitter delegate の bootstrap 段階
   - 2026-04-03: bootstrap emitter に `ClosureDef -> FunctionDef` の互換変換を追加し、`test/fixture/source/py/control/nested_closure_def.py` の Julia emit failure を解消
   - 2026-04-03: `tools/unittest/emit/julia/test_py2julia_smoke.py` が `juliaup` launcher ではなく実体バイナリを優先するように修正し、39 tests `OK (skipped=1)` を再確認
   - 2026-04-03: toolchain2 Julia emitter 内で bootstrap rewrite を `JuliaBootstrapRewriter`、旧 emitter delegate を `JuliaLegacyEmitterBridge` に分離し、`render_module()` 入口を明示化
   - 2026-04-03: `render_module()` 前処理を `_prepare_module_for_emit()` に切り出し、cross-module default expansion を入力 doc の deep copy に対してだけ適用するよう修正。非破壊性を unit test で確認
   - 2026-04-03: bootstrap helper を `src/toolchain2/emit/julia/bootstrap.py` へ分離し、`emitter.py` は renderer 入口と orchestration に集中する構成へ整理
   - 2026-04-03: `module_id_from_doc()` / `prepare_module_for_emit()` も `bootstrap.py` へ移し、bootstrap helper を renderer 本体から分離
   - 2026-04-03: `src/toolchain2/emit/julia/subset.py` を追加し、`add/assign/compare/if_else` 相当の狭い AST subset は legacy bridge を通さず toolchain2-native に emit できる経路を追加
   - 2026-04-03: subset native renderer に `AnnAssign` と `ForCore` (`StaticRangeForPlan` / `RuntimeIterForPlan`) を追加し、`for_range` / `loop` 相当まで toolchain2-native coverage を拡張
   - 2026-04-03: subset native renderer に `BoolOp` と `IfExp` を追加し、`ifexp_bool` 相当も toolchain2-native path で処理できるようにした
   - 2026-04-03: subset native renderer に membership / slice / list repeat と `dict.get` / tuple `Swap` / `str.join` を追加し、`dict_in`, `negative_index`, `slice_basic`, `list_repeat`, `dict_literal_entries`, `tuple_assign`, `str_join_method` を native path へ乗せた
   - 2026-04-03: subset native renderer に `Lambda` を追加し、`lambda_basic`, `lambda_immediate`, `lambda_ifexp`, `lambda_as_arg`, `lambda_capture_multiargs`, `lambda_local_state` を native path へ乗せた。現時点の native coverage は `core` 19件、`control` 7件
   - 2026-04-03: subset 判定を bootstrap rewrite 後に寄せ、空 `ClassDef` は no-op として扱うよう整理。`class_tuple_assign` と `nested_closure_def` も native path に乗るようになり、現時点の native coverage は `core` 20件、`control` 8件
   - 2026-04-03: subset native renderer に最小 class support を追加し、empty class・simple `__init__`・class call・instance field access を native 化。`class_body_pass` と `obj_attr_space` を native path へ乗せ、現時点の native coverage は `core` 22件、`control` 8件
   - 2026-04-03: subset native renderer に `While` を追加し、generator lowering 後の `yield_generator_min` を native path へ乗せた。現時点の native coverage は `core` 22件、`control` 9件
   - 2026-04-03: subset native renderer に `Try` / `Raise` を追加し、`try_raise`, `finally`, `exception_bare_reraise`, `exception_finally_order`, `exception_propagation_raise_from`, `exception_propagation_two_frames` を native path へ乗せた。残る control 側の legacy 依存は `exception_user_defined_multi_handler` のみ
   - 2026-04-03: subset native renderer に custom exception class の最小 support を追加し、`exception_user_defined_multi_handler` も native path へ乗せた。現時点の native coverage は `core` 22件、`control` 16件
   - 2026-04-03: Julia の emitter 検証は emitter guide に従い `runtime_parity_check_fast.py` と smoke parity を正本とし、専用 bootstrap unit test は持たない方針へ戻した
   - 2026-04-03: `runtime_parity_check_fast.py` の Julia 実行経路は `juliaup` launcher ではなく実体バイナリを優先するよう修正し、subset native renderer 側でも `str(...)` と negative-step `range(...)` を吸収して `fixture/control` parity 16/16 を再確認
   - 2026-04-03: subset native renderer に `ImportFrom(math/time/pytra.utils.png)` と `int` / `bytearray` の最小 mapping、Julia 予約語 identifier mangle を追加し、`from_import_symbols` と `import_time_from` を native path へ乗せた
   - 2026-04-03: subset native renderer に `str` method (`strip/rstrip/startswith/endswith/replace/join`)、list mutation (`clear/sort/reverse`)、`JoinedStr` / `FormattedValue` を追加し、`str_methods`, `list_mutation_methods`, `fstring` を native path へ乗せた
   - 2026-04-03: subset native renderer に `pytra.std.collections.deque` import と `deque`/`dict` mutation (`appendleft/popleft/pop/clear/setdefault`) を追加し、`deque_basic` と `dict_mutation_methods` を native path へ乗せた
   - 2026-04-03: subset native renderer に `str` extended method (`lower/find/index/isalnum/lstrip/split`) を追加し、`str_methods_extended` も native path へ乗せた
   - 2026-04-03: subset native renderer に `Import(math)` と `ImportFrom(pytra.std.math)` を追加し、module attr call (`sqrt/floor/fabs`) も許可して `import_math_module` と `from_pytra_std_import_math` を native path へ乗せた
   - 2026-04-03: subset native renderer に `Import(pytra.std.env/os, pytra.utils.png)` と keyword `os.makedirs(..., exist_ok=...)`、`str + str` 連結を追加し、`import_pytra_runtime_png` を native path へ乗せた
   - 2026-04-03: subset native renderer に `VarDecl` / `Set` / expression `range(...)` / `reversed(...)` と membership の `__pytra_contains` lowering を追加し、`enumerate_basic`, `reversed_enumerate`, `in_membership_iterable` を native path へ乗せた
   - 2026-04-03: subset native renderer に `set.add`, `dict.keys/values`, `bytearray[...] = ...` を追加し、`set_mutation_methods`, `dict_wrapper_methods`, `bytearray_basic` を native path へ乗せた
   - 2026-04-03: subset native renderer に `set.discard/remove` と builtin `set()` を追加し、`set_wrapper_methods` と `nested_types` を native path へ乗せた
   - 2026-04-03: subset native renderer に `dict.items()` と `list.extend()` を追加し、`typed_container_access` を native path へ乗せた
   - 2026-04-03: `object_container_access` が既存 subset の組み合わせ (`dict.items/get`, `list.extend`, tuple-in-set, union container access) で native path / parity PASS になることを確認
   - 2026-04-03: subset native renderer に property getter / instance method を含む最小 class support を追加し、`property_method_call` を native path へ乗せた
   - 2026-04-03: subset native renderer に bitwise `~`, `&`, `|`, `^` を追加し、`bitwise_invert_basic` を native path へ乗せた
   - 2026-04-03: subset native renderer に `@staticmethod` class support を追加し、`staticmethod_basic` を native path へ乗せた
   - 2026-04-04: subset native renderer に instance field `AugAssign` (`self.field += ...`) を追加し、`class_instance` を native path へ乗せた
   - 2026-04-04: bootstrap rewrite が class body の `AnnAssign` static attr も global へ lift するよう修正し、`class_member` を native path へ乗せた
   - 2026-04-04: subset native renderer が object parameter field update (`x.v += ...`) も扱えるようになり、`alias_arg` を native path へ乗せた
   - 2026-04-04: subset native renderer に `IsInstance` の Julia type mapping (`PYTRA_TID_*`, `dict/list/tuple/set/str/int/float/bool`) を追加し、`union_basic`, `union_dict_items`, `isinstance_pod_exact`, `isinstance_tuple_check` を native path へ乗せた
   - 2026-04-04: subset native renderer に type-only `ImportFrom(pytra.std.json)`、`str.isdigit()`、`Expr(Name("continue"|"break"))` の吸収を追加し、`union_return_errorcheck` と `isinstance_narrowing` も native path / parity PASS に寄せた
   - 2026-04-04: subset native renderer に `TypeAlias` no-op と `str.upper()` を追加し、`type_alias_pep695` と `callable_higher_order` を native path / parity PASS に寄せた
   - 2026-04-04: subset native renderer の `str(...)` / `bool(...)` / `str.isdigit()` を Julia runtime helper (`__pytra_str`, `__pytra_truthy`, `__pytra_str_isdigit`) に揃え、`union_list_mixed` を native path / parity PASS に寄せた
   - 2026-04-04: subset native renderer に bit shift (`<<`, `>>`) を追加し、`starred_call_tuple_basic` を native path / parity PASS に寄せた
   - 2026-04-04: subset native renderer が `pytra.enum` import と空 enum class (`Enum`, `IntEnum`, `IntFlag`) を受けられるようになり、`enum_basic`, `intenum_basic`, `intflag_basic` を native path / parity PASS に寄せた
   - 2026-04-04: subset native renderer に tuple/list destructuring assign と nested/subscript target unpack を追加し、`tuple_unpack_variants` を native path / parity PASS に寄せた
   - 2026-04-04: subset native renderer に single-generator の `ListComp` / `SetComp` / `DictComp` と list concat (`vcat`) を追加し、`ok_list_concat_comp`, `comprehension_dict_set`, `comprehension_nested` を native path / parity PASS に寄せた
   - 2026-04-04: subset native renderer が linked 後の typed-vararg 形 (`arg_order` + `vararg_name`) を受けられるようになり、値なし `AnnAssign` と `Attribute` target の plain `Assign` も吸収して `ok_typed_varargs_representative` を native path / parity PASS に寄せた
2. [x] [ID: P1-JULIA-EMITTER-S2] `src/runtime/julia/mapping.json` を作成する — `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` を定義
   - 2026-04-02: `src/runtime/julia/mapping.json` を追加し、toolchain2 Julia emitter bootstrap が参照する runtime call/type mapping を整備
3. [x] [ID: P1-JULIA-EMITTER-S3] fixture 全件の Julia emit 成功を確認する
   - 2026-04-02: `check_py2x_transpile.py --target julia` の代表 3 件（`core/add`, `control/if_else`, `control/for_range`）で emit 成功を確認
   - 2026-04-03: `collections` 先頭群から `oop` / `signature` 前半までを順次確認し、少なくとも 90 件超で Julia emit 成功を確認
   - 2026-04-03: `oop/trait_basic.py`, `oop/trait_with_inheritance.py`, `signature/ok_fstring_format_spec.py` は Julia emitter ではなく frontend/linker 側で失敗することを確認
   - 2026-04-03: `control/exception_bare_reraise.py`, `control/exception_propagation_raise_from.py`, `control/exception_propagation_two_frames.py`, `control/exception_user_defined_multi_handler.py` は Julia emit+run parity まで復旧
4. [x] [ID: P1-JULIA-EMITTER-S4] Julia runtime を toolchain2 の emit 出力と整合させる
   - 2026-04-03: `src/runtime/julia/` に `std/json.jl`, `std/sys.jl`, `std/argparse.jl`, `std/pathlib.jl`, `utils/png.jl` を追加し、`py_runtime.jl` の Python 互換 helpers・例外・truthiness・文字列/bytes/container 表現を補強
   - 2026-04-03: emitter 側の runtime alias/include 解決を整理し、`pytra.std` / `pytra.utils` import と stdlib runtime の Julia 出力を整合させた
5. [x] [ID: P1-JULIA-EMITTER-S5] fixture の Julia run parity を通す（`julia`）
   - 2026-04-03: `tools/unittest/emit/julia/test_py2julia_smoke.py` の parity 28 件が PASS（`skipped=1`）
   - 2026-04-03: `runtime_parity_check_fast.py --case-root fixture --targets julia add fib if_else for_range` で 4/4 PASS
   - 2026-04-03: exception 系 4 件のうち 3 件（`exception_bare_reraise`, `exception_propagation_raise_from`, `exception_propagation_two_frames`）が PASS。`exception_user_defined_multi_handler` は Julia runtime/class 連携の残課題
   - 2026-04-03: exception/custom-exception path を修正し、`runtime_parity_check_fast.py --case-root fixture --targets julia --category control` が 16/16 PASS
   - 2026-04-03: `runtime_parity_check_fast.py --case-root fixture --targets julia --category core` が 22/22 PASS
   - 2026-04-03: `staticmethod_basic` を PASS 化。残る主要課題は concrete class 継承 (`class_inherit_basic`, `inheritance*`, `is_instance`, `super_init`) と trait 系 typed varargs
   - 2026-04-03: Julia class inheritance model を `abstract type + backing struct` に寄せ、`class_inherit_basic`, `inheritance`, `inheritance_polymorphic_dispatch`, `inheritance_virtual_dispatch_multilang`, `is_instance`, `isinstance_user_class`, `super_init` を PASS 化
   - 2026-04-03: `runtime_parity_check_fast.py --case-root fixture --targets julia --category oop` は 19 件中 16 件 PASS。残りは `trait_basic`, `trait_with_inheritance` の typed `*args` 制約と、`extern_opaque_basic` の python 側 failure
   - 2026-04-03: trait bootstrap を追加し、`trait_basic` / `trait_with_inheritance` を PASS 化
   - 2026-04-03: import/include path と Julia runtime alias を修正し、`from_import_symbols`, `from_pytra_std_import_math`, `import_time_from`, `negative_index_out_of_range`, `deque_basic`, `set_mutation_methods`, `set_wrapper_methods`, `property_method_call`, `enum_basic`, `intenum_basic`, `intflag_basic`, `exception_user_defined_multi_handler` を PASS 化
   - 2026-04-03: Julia runtime に `utils/png.jl` と Python 互換 `__pytra_str` / `__pytra_str_slice` を追加し、`import_pytra_runtime_png`, `callable_higher_order`, `for_over_string`, `nested_types`, `object_container_access`, `ok_class_inline_method`, `ok_list_concat_comp`, `ok_multi_for_comp`, `str_methods_extended`, `str_repr_containers`, `str_slice`, `tuple_unpack_variants` を PASS 化
   - 2026-04-03: `ok_fstring_format_spec`, `ok_generator_tuple_target`, `ok_typed_varargs_representative` を復旧し、`runtime_parity_check_fast.py --case-root fixture --targets julia` が 145/145 PASS
6. [x] [ID: P1-JULIA-EMITTER-S6] stdlib の Julia parity を通す（`--case-root stdlib`）
   - 2026-04-03: `runtime_parity_check_fast.py --case-root stdlib --targets julia` が 16/16 PASS
   - 2026-04-03: `json_indent_optional`, `json_unicode_escape`, `math_path_runtime_ir`, `os_glob_extended`, `pathlib_extended`, `re_extended`, `sys_extended` を Julia runtime / import alias / Path lowering 対応で復旧
7. [x] [ID: P1-JULIA-EMITTER-S7] sample の Julia parity を通す（`--case-root sample`）
   - 2026-04-03: `runtime_parity_check_fast.py --case-root sample --targets julia` が 18/18 PASS
   - 2026-04-03: 画像生成系 sample の artifact parity も確認し、`01_mandelbrot` から `18_mini_language_interpreter` まで Julia で完走

### P2-JULIA-LINT: emitter hardcode lint の Julia 違反を解消する

1. [x] [ID: P2-JULIA-LINT-S1] `check_emitter_hardcode_lint.py --lang julia` で全カテゴリ 0 件になることを確認する
   - 2026-04-02: `python3 tools/check/check_emitter_hardcode_lint.py --lang julia` で全カテゴリ 0 件を確認
