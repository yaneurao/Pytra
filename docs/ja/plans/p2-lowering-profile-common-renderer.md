<a href="../../en/plans/p2-lowering-profile-common-renderer.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2-LOWERING-PROFILE: Lowering プロファイル + CommonRenderer 導入

最終更新: 2026-03-28
ステータス: 進行中

## 背景

現在各言語の emitter は EAST3 ノード走査ロジックをそれぞれフルに実装しているが、大部分は構造的に同一（If/While/BinOp/Call/Return 等）。言語間の違いは主に構文トークンと一部の構造差である。

また、EAST3 の lowering が単一の形状（例: tuple unpack を Subscript に展開）を生成するため、Go のように tuple 型がない言語で問題が起きている。言語の能力に応じた lowering が必要。

## 設計

### Lowering プロファイル

各言語が CodeEmitter のプロファイル JSON で言語能力を宣言する。EAST3 lowering がこれを参照して言語に合った形状を生成する。

主要プロファイル項目:
- `tuple_unpack_style`: subscript / structured_binding / pattern_match / multi_return / individual_temps
- `container_covariance`: true / false
- `closure_style`: native_nested / closure_syntax
- `with_style`: raii / try_with_resources / using / defer / try_finally
- `property_style`: field_access / method_call
- `swap_style`: std_swap / multi_assign / mem_swap / temp_var

### CommonRenderer

EAST3 ノード走査の共通基底クラス。プロファイルの構文テーブル（type_map, operator_map, syntax）を参照してコード生成する。各言語 emitter は CommonRenderer を継承し、言語固有のノード（FunctionDef, ClassDef, For 等）だけ override する。

詳細は spec-language-profile.md §7〜§8 を参照。

## サブタスク

1. [ID: P2-LOWERING-PROFILE-S1] lowering プロファイルのスキーマを確定し、C++ / Go のプロファイル JSON を作成する
2. [ID: P2-LOWERING-PROFILE-S2] EAST3 lowering が lowering プロファイルを読み、`tuple_unpack_style` に従って tuple unpack を展開するようにする
3. [ID: P2-LOWERING-PROFILE-S3] `container_covariance` / `with_style` / `property_style` を lowering に反映する
4. [ID: P2-LOWERING-PROFILE-S4] CommonRenderer 基底クラスを実装する（If/While/BinOp/Call/Return/Assign 等の共通ノード走査）
5. [ID: P2-LOWERING-PROFILE-S5] C++ emitter を CommonRenderer + override 構成に移行する
6. [ID: P2-LOWERING-PROFILE-S6] Go emitter を CommonRenderer + override 構成に移行する
7. [ID: P2-LOWERING-PROFILE-S7] 既存 fixture + sample の全言語 parity が維持されることを確認する

## 進捗メモ

- 2026-03-28: [ID: P2-LOWERING-PROFILE-S1] 正本 profile 配置を `src/toolchain2/emit/profiles/` に統一し、`core.json`, `cpp.json`, `go.json` を参照する `toolchain2.emit.common.profile_loader` と focused unittest を追加した。`tuple_unpack_style` / `container_covariance` / `closure_style` / `with_style` / `property_style` / `swap_style` の schema validation と core merge を固定した。
- 2026-03-28: [ID: P2-LOWERING-PROFILE-S2] `lower_east2_to_east3(..., target_language=...)` が lowering profile を読むようにし、tuple unpack を `core=individual_temps`, `cpp=TupleUnpack`, `go=MultiAssign` へ分岐するようにした。あわせて Go emitter で `multi_return[...]` の関数署名 / return / multi-assign を最小限 consume できるようにし、focused unittest で target ごとの EAST3 と emit を固定した。
- 2026-03-28: [ID: P2-LOWERING-PROFILE-S3] `container_covariance` / `with_style` / `property_style` を lowering に反映した。`container_covariance=false` では `CovariantCopy` を生成し、`with_style=try_finally` では `With` を bind + `Try(finally close)` に lower、`property_style=field_access` では `attribute_access_kind="property_getter"` を field access へ正規化する。C++ / Go emitter には `CovariantCopy` の最小消費を追加し、focused unittest で固定した。
- 2026-03-28: [ID: P3-COMMON-RENDERER-S1] `toolchain2.emit.common.common_renderer.CommonRenderer` を追加し、profile JSON の `operators` / `syntax` / `lowering` を読む共通 expr/stmt walk を実装した。`Constant/Name/BinOp/UnaryOp/Compare/BoolOp/Expr/Return/If/While` は基底で処理し、`Call/Attribute/Assign` は hook として残している。dummy renderer unittest で C++ / Go profile の構文差分を固定した。

## 受け入れ基準

1. C++ / Go の lowering プロファイルが JSON で宣言されていること
2. tuple unpack が言語プロファイルに従って lowering されること（Go: multi_return / individual_temps）
3. CommonRenderer が共通ノードを処理し、C++ / Go emitter が override のみで構成されていること
4. 既存 fixture + sample の parity が維持されること

## 決定ログ

- 2026-03-28: Go emitter の tuple unpack 問題を契機に、言語能力の宣言（lowering プロファイル）と共通 renderer の設計を議論。spec-language-profile.md §7〜§8 に追記。
