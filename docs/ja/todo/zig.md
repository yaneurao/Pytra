<a href="../../en/todo/zig.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Zig backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-10

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/zig/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/zig/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の Zig emitter: `src/toolchain/emit/zig/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の Zig runtime: `src/runtime/zig/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-ZIG-COMMON-RENDERER-EXC: `with` / 例外 lowering を CommonRenderer へ押し戻す

文脈: [docs/ja/plans/p0-zig-rs-common-renderer-exceptions.md](../plans/p0-zig-rs-common-renderer-exceptions.md)

1. [x] [ID: P0-ZIG-CREXC-S1] Rust の `with` lowering を CommonRenderer 正本へ戻し、`with_statement` / `with_context_manager` parity を維持する
2. [x] [ID: P0-ZIG-CREXC-S2] Zig の `with` lowering を CommonRenderer 正本へ戻し、`with_statement` / `with_context_manager` parity を維持する
3. [x] [ID: P0-ZIG-CREXC-S3] CommonRenderer に exception strategy hook を追加し、Rust / Zig の `try` / `raise` を hook 実装へ分離する
4. [ ] [ID: P0-ZIG-CREXC-S4] Rust / Zig の `exception_types` / `try_raise` / `exception_bare_reraise` parity を維持したまま custom lowering を縮小する
   進捗: `with` の alias hoist / file lane は CommonRenderer hook 化済み。Rust は `Try` statement entry、`catch_unwind` wrapper、`resume_unwind`、handler dispatch 骨格、user-defined exception raise の `panic_any`、一般 `panic!(...)`、`__try_*` / `__with_*` / `__catch_*` / `__err_*` 固定 temp 名まで CommonRenderer hook 経由に移行済み。さらに `with` custom path では hoist 収集、protocol call builder、bind/clone 分岐、`__exit__` / `close()` fallback、entry tuple と exit target 選択、item metadata 解決、context capture、bound target naming、`with_enter_runtime_call`、enter/exit fallback predicate、bound 変数の新規宣言判定と state registration、outer wrapper、hoisted binding 宣言まで CommonRenderer helper に移行し、`With` の direct custom path も削除して renderer entry に一本化した。Zig は handler dispatch loop、`try`/`with` body post-stmt propagation、body/orelse wrapper、bare re-raise restore、raise propagation、raise state writes、handler capture、global exception slot 宣言、slot 名そのものの抽象化、bound exception value、active exception type slot accessまで CommonRenderer helper / accessor に移行済み。さらに guarded/simple block expr helper への移行で `str.index` / bounds-check index / list concat / list repeat / tuple-list literal / splitext / sum / zip / comprehension / compare callable block を共通 skeleton に寄せ、fallback `with` でも `__enter__` bind、fallback `__enter__` / `__exit__` / `file_close`、`TextIOWrapper` bind、body 展開を helper 経由へ統一した。dispatch condition / handler guard condition / propagation check / labeled block primitive / `try` wrapper の handler/orelse/finalbody も CommonRenderer 側へ整理済み。`lowering.exception_style` も `rs/zig` profile に反映済み。
   残件: Zig 側は manual exception slot を Zig 構文へ写す最終 adapter、すなわち slot 名、exception match 条件、labeled block / `break :label`、fallback `with` protocol call、handler prelude/teardown の整理が中心。Rust 側の大きい custom orchestration はほぼ吸収済み。

### P0-ZIG-TOOLCHAIN-LEGACY: toolchain_ 依存を解消する

`src/toolchain/emit/zig/emitter.py` が旧 toolchain（`toolchain_`）の `runtime_symbol_index` を参照している。`toolchain_` は deprecated で今後削除される。

依存箇所: `from toolchain_.frontends.runtime_symbol_index import canonical_runtime_module_id, lookup_runtime_module_symbols`

1. [ ] [ID: P0-ZIG-LEGACY-S1] `runtime_symbol_index` の必要な機能を toolchain 側に移行するか、emitter 内で EAST3 メタデータから直接取得するように修正する
2. [ ] [ID: P0-ZIG-LEGACY-S2] `toolchain_` への import がゼロになることを確認する

### P0-ZIG-NEW-FIXTURE-PARITY: 新規追加 fixture / stdlib の parity 確認

今セッション（2026-04-01〜05）で追加・更新した fixture と stdlib の parity を確認する。

対象: `bytes_copy_semantics`, `negative_index_comprehensive`, `negative_index_out_of_range`, `callable_optional_none`, `str_find_index`, `eo_extern_opaque_basic`(emit-only), `math_extended`(stdlib), `os_glob_extended`(stdlib)

1. [ ] [ID: P0-ZIG-NEWFIX-S1] 上記 fixture/stdlib の parity を確認する（対象 fixture のみ実行）
