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
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] bootstrap rewrite の責務を toolchain2 側に固定するため、互換変換の単体テストを追加した。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] smoke parity は `juliaup` launcher 依存を避け、実体バイナリを優先して再現性を上げた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] toolchain2 側で `JuliaBootstrapRewriter` と `JuliaLegacyEmitterBridge` を分離し、rewrite と legacy emit の責務境界を明示した。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] emit 前処理を `_prepare_module_for_emit()` に切り出し、default expansion を入力非破壊で行うよう整理した。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] bootstrap helper を `bootstrap.py` に分離し、renderer 本体から移行用実装詳細を切り離した。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] `module_id_from_doc()` / `prepare_module_for_emit()` を bootstrap module へ移し、renderer private helper を経由しない direct bootstrap tests に切り替えた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] `subset.py` に狭い toolchain2-native Julia renderer を追加し、単純 module は legacy bridge を使わず emit する最初の移行経路を作った。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `ForCore` / `AnnAssign` を追加し、`for_range` / `loop` を native path で処理できるようにした。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `BoolOp` / `IfExp` を追加し、`ifexp_bool` を native path へ乗せた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に membership / slice / list repeat と `dict.get` / tuple `Swap` / `str.join` を追加し、core/control の単純 fixture coverage を広げた。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] 空 class は subset にまだ載せず legacy bridge を維持する。`ClassDef` を早期に native 化すると既存 Julia smoke contract と衝突したため、段階移行を優先する。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に `Lambda` を追加し、匿名関数と capture を含む core fixture 群を native path へ移した。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset 判定を bootstrap rewrite 後に寄せ、空 `ClassDef` を no-op として扱う段階移行に切り替えた。これで static class attr と closure rewrite 後の一部 fixture も native path に含められる。
- 2026-04-03: [ID: P1-JULIA-EMITTER-S1] subset native renderer に最小 class support を追加し、empty class・simple `__init__`・class call・instance field access を native 化した。
