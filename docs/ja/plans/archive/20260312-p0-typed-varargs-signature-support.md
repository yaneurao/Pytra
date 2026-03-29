<a href="../../../en/plans/archive/20260312-p0-typed-varargs-signature-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: typed `*args` signature を representative C++ lane で通す

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-TYPED-VARARGS-SIGNATURE-01`

背景:
- 現在の self-hosted parser は function signature の `*args` / `**kwargs` を明示的に reject している。
- 代表例として Pytra-NES の `def merge_controller_states(target: ControllerState, *states: ControllerState) -> None:` は `Use explicit parameters instead of *args.` で止まる。
- 現状の EAST `FunctionDef` carrier は `arg_types` / `arg_order` / `arg_defaults` しか持たず、variadic positional parameter の情報を保持できない。
- parser だけを通しても call site 側の extra positional arg packing が無ければ runtime / emitter で壊れる。

目的:
- representative v1 として、typed user-defined `*args` signature を self-hosted parser から C++ target まで通す。
- `def f(x: T, *rest: U) -> R` を受理し、known user function call で extra positional arg を trailing collection parameter へ pack できるようにする。
- C++ 以外の backend は v1 では silent fallback せず fail-closed を維持する。

対象:
- self-hosted signature parser の typed `*args: T` support
- `FunctionDef` / signature carrier への `vararg_name` / `vararg_type` / `vararg_type_expr` 追加
- stmt/module parser・builder・frontend mirror の signature field 追従
- representative user-defined function call の arg packing
- C++ emitter の function definition / call emit
- representative regression fixture と source-contract
- ja/en TODO / plan / docs 同期

非対象:
- untyped `*args`
- `**kwargs`
- positional-only `/`
- keyword-only `*` marker の追加拡張
- starred actual argument `f(*xs)` の新規実装
- Rust/C#/他 backend の本実装

受け入れ基準:
- self-hosted parser が `def f(x: T, *rest: U) -> R:` を受理し、`FunctionDef` に variadic positional metadata を保持できること。
- representative fixture で extra positional arg call が trailing collection parameter へ pack され、C++ transpile と runtime regression が通ること。
- non-C++ backend は representative `*args` lane を fail-closed に維持し、誤った silent emit をしないこと。
- unsupported lane（untyped `*args`, `**kwargs`）は引き続き明示的に reject されること。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_self_hosted_signature.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east1_build.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k varargs`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_east3_cpp_bridge.py' -k varargs`
- `python3 tools/build_selfhost.py`
- `python3 tools/check/check_transpiler_version_gate.py`
- `python3 tools/run/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

決定ログ:
- 2026-03-11: v1 は `typed *args: T` の user-defined function に限定し、call site packing は C++ representative lane だけを実装する。
- 2026-03-11: IR carrier は dedicated `vararg_*` field を追加し、`arg_order` に variadic parameter を混ぜて疑似的に表現しない。
- 2026-03-11: non-C++ backend は support を装わず、representative lane を fail-closed に保つ。

## 分解

- [x] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S1-01] current reject contract と representative fixture を固定し、typed `*args` v1 scope を docs/test に落とす。
- [x] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S2-01] self-hosted signature parser / AST builder / stmt/module parser に `vararg_*` field を追加し、`FunctionDef` carrier へ通す。
- [x] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S2-02] frontend mirror / auxiliary schema へ `vararg_*` field を追従させ、selfhost regression を固める。
- [x] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S3-01] C++ emitter の function definition / known call lane に variadic positional packing を追加し、representative fixture を通す。
- [x] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S3-02] non-C++ backend contract guard と docs を更新して v1 を閉じる。

- 2026-03-11: representative blocker fixture `ng_typed_varargs_representative.py` を追加し、typed `*args` が現状 reject であることを unit test で固定した。
- 2026-03-11: `typed *args: T` は `FunctionDef.vararg_name/vararg_type/vararg_type_expr` に保持し、body scope では `list[T]` として公開する方針にした。
- 2026-03-11: representative fixture は `ok_typed_varargs_representative.py` へ反転し、untyped `*args` reject は `ng_varargs.py` に戻した。
- 2026-03-11: frontend mirror と host signature extractor でも `vararg_*` を dedicated field として保持し、`arg_order` / `arg_types` に variadic parameter を混ぜない方針を固定した。
- 2026-03-11: C++ v1 では `*rest: T` を trailing `list[T]` parameter として署名化し、known user-function call の extra positional arg は synthetic `List` node を call-arg bridge に通して `rc_list_from_value(...)` まで coercion する。
- 2026-03-11: representative lane では top-level known function の mutable parameter position を prescan して、caller 側の `ControllerState&` などの mutability も interprocedural に反映する。
- 2026-03-11: non-C++ backend は shared `reject_backend_typed_vararg_signatures()` を transpile entrypoint に通し、typed `*args` を `unsupported_syntax` で fail-closed に統一する。
