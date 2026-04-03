<a href="../../en/plans/p1-julia-emitter.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1-JULIA-EMITTER

最終更新: 2026-04-03

## 対象

- [ID: P1-JULIA-EMITTER-S1] `src/toolchain2/emit/julia/` に Julia emitter を新規実装する
- [ID: P1-JULIA-EMITTER-S2] `src/runtime/julia/mapping.json` を作成する

## 目的

- 旧 `src/toolchain/emit/julia/` を今後の修正対象から外し、toolchain2 側に Julia backend の正本を用意する。
- emitter 実装ガイドラインに沿って、profile / mapping / emitter 入口を toolchain2 の標準構成へ揃える。

## 方針

- 第1段階では、toolchain2 側に `CommonRenderer` ベースの Julia emitter 入口を追加する。
- 既存 parity を不用意に壊さないため、bootstrap 期は旧 Julia emitter を互換 delegate として利用しつつ、新規実装の受け皿を toolchain2 側へ固定する。
- runtime 関数名・型名・target 定数は `src/runtime/julia/mapping.json` に集約する。
- 演算子や構文の基礎設定は `src/toolchain2/emit/profiles/julia.json` に置く。

## 完了条件

- `src/toolchain2/emit/julia/` が import 可能である。
- `src/runtime/julia/mapping.json` が存在し、最低限の `builtin_prefix` / `calls` / `types` / `skip_modules` / `implicit_promotions` を持つ。
- bootstrap emitter から Julia ソース文字列を生成できる。

## 決定ログ

- 2026-04-02: [ID: P1-JULIA-EMITTER-S1] Julia backend の新規実装先を `src/toolchain2/emit/julia/` に固定し、bootstrap 期は旧 emitter への delegate で移行を開始する。
- 2026-04-02: [ID: P1-JULIA-EMITTER-S2] runtime call/type の正本を `src/runtime/julia/mapping.json` に新設し、profile-driven emitter へ移行する準備を行う。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] smoke parity は `juliaup` launcher 依存を避け、実体バイナリを優先して再現性を上げた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] toolchain2 側で `JuliaBootstrapRewriter` と `JuliaLegacyEmitterBridge` を分離し、rewrite と legacy emit の責務境界を明示した。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] emit 前処理を `_prepare_module_for_emit()` に切り出し、default expansion を入力非破壊で行うよう整理した。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] bootstrap helper を `bootstrap.py` に分離し、renderer 本体から移行用実装詳細を切り離した。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] `module_id_from_doc()` / `prepare_module_for_emit()` を bootstrap module へ移し、renderer 本体から移行用 helper を分離した。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] `subset.py` に狭い toolchain2-native Julia renderer を追加し、単純 module は legacy bridge を使わず emit する最初の移行経路を作った。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `ForCore` / `AnnAssign` を追加し、`for_range` / `loop` を native path で処理できるようにした。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `BoolOp` / `IfExp` を追加し、`ifexp_bool` を native path へ乗せた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に membership / slice / list repeat と `dict.get` / tuple `Swap` / `str.join` を追加し、core/control の単純 fixture coverage を広げた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] 空 class は subset にまだ載せず legacy bridge を維持する。`ClassDef` を早期に native 化すると既存 Julia smoke contract と衝突したため、段階移行を優先する。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `Lambda` を追加し、匿名関数と capture を含む core fixture 群を native path へ移した。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset 判定を bootstrap rewrite 後に寄せ、空 `ClassDef` を no-op として扱う段階移行に切り替えた。これで static class attr と closure rewrite 後の一部 fixture も native path に含められる。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に最小 class support を追加し、empty class・simple `__init__`・class call・instance field access を native 化した。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `While` を追加し、generator lowering 後の control fixture も native path に取り込んだ。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `Try` / `Raise` を追加し、標準例外と finally を使う control fixture 群を native path に移した。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に custom exception class の最小 support を追加し、fixture/control は native path で全件処理できる段階まで寄せた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] emitter の検証は guide に従い parity check 正本へ戻し、専用 bootstrap unit test は持たない方針に修正した。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] parity runner の Julia 実行は実体バイナリ優先へ寄せ、subset native renderer でも `str(...)` と negative-step `range(...)` を吸収して control parity 16/16 を維持した。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `ImportFrom(math/time/pytra.utils.png)` と `int` / `bytearray` の最小 mapping、Julia 予約語 identifier mangle を追加し、単純 import fixture も native path へ寄せ始めた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `str` method 群、list mutation、`JoinedStr` / `FormattedValue` を追加し、単純 string/list fixture も native path へ寄せた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `pytra.std.collections.deque` import と deque/dict mutation を追加し、単純 collections fixture も native path へ広げた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `str` extended method 群（`lower/find/index/isalnum/lstrip/split`）を追加し、追加の string fixture も native path へ寄せた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `Import(math)` と `ImportFrom(pytra.std.math)` を追加し、math module / symbol import fixture も native path に寄せた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `Import(pytra.std.env/os, pytra.utils.png)` と keyword `os.makedirs(..., exist_ok=...)`、文字列連結の Julia 化を追加し、PNG import fixture も native path に寄せた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `VarDecl` / `Set` / expression `range(...)` / `reversed(...)` と membership の `__pytra_contains` lowering を追加し、`enumerate_basic`, `reversed_enumerate`, `in_membership_iterable` も native path に寄せた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `set.add`, `dict.keys/values`, `bytearray[...] = ...` を追加し、`set_mutation_methods`, `dict_wrapper_methods`, `bytearray_basic` も native path に寄せた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `set.discard/remove` と builtin `set()` を追加し、`set_wrapper_methods` と `nested_types` も native path に寄せた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `dict.items()` と `list.extend()` を追加し、`typed_container_access` も native path に寄せた。
