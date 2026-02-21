# TODO（未完了）

<a href="../docs/todo.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-22

## 実行順（上から着手）

1. `P3: py2rs（EAST移行）を CodeEmitter 中心で再設計`
2. `P4: 他言語トランスパイラの EAST 移行`

## Yanesdk 再調査メモ（2026-02-22）

- 調査対象: `Yanesdk/` 配下の `.py` 16ファイル（library 8 / game 7 / browser-shim 1）
- 現状結果（2026-02-22）:
  - EAST 変換（`convert_path`）成功 `9/16`、失敗 `7/16`（`docs/*/yanesdk.py` の文末 `;`）。
  - canonical 対象（`library 1本 + game 7本`）の `py2cpp.py` 変換は `8/8` 成功。
- `py2cpp` で通す対象:
  - `Yanesdk/yanesdk/yanesdk.py`（正本 library）
  - `Yanesdk/docs/*/*.py` のゲーム本体（`yanesdk.py` 重複コピーは除外）
- `;` について:
  - `Yanesdk` 側の文法誤りとして扱う。self_hosted parser では受理しない（サポート対象外）。
- `browser` / `browser.widgets.dialog` について:
  - Brython が提供する薄い wrapper であり、最終的には JavaScript 側の `document/window/canvas` などへ直接接続して動かす前提。
  - そのため `py2js` では「モジュール本体を変換する」のではなく「外部提供ランタイム（ブラウザ環境）への参照」として扱う方針にする。
- 正本ファイル運用:
  - `yanesdk.py` は `Yanesdk/yanesdk/yanesdk.py` を正本として扱う。
  - `Yanesdk/docs/*/yanesdk.py` は重複コピーとして扱い、解析・修正の基準にしない。

## P3: py2rs（EAST移行）を CodeEmitter 中心で再設計（Yanesdk対応後）

- 着手条件: 本セクションは `P0/P1-A/P1-B/P2` が完了するまで着手しない。
- 優先順: `Yanesdk` の構文サポートと import 解決を先に完了し、その後に `py2rs` へ着手する。

1. [x] 方針固定: `py2rs.py` は「CLI + 入出力 + 依存解決」の薄いオーケストレータに限定する。
   - [x] Rust 固有の式/文変換ロジックは `src/hooks/rs/emitter/rs_emitter.py` へ分離する。
   - [x] `src/common/` と `src/rs_module/` には依存しない。
2. [ ] `CodeEmitter` の責務拡張を先に実施する（py2rs実装より先）。
   - [ ] `py2cpp.py` と `py2rs.py` で共通化できる EAST ユーティリティ（型変換補助・import束縛・文/式ディスパッチ補助）を `src/pytra/compiler/east_parts/code_emitter.py` へ移す。
     - [x] import 束縛ローダ `load_import_bindings_from_meta()` を `CodeEmitter` へ移管。
     - [x] tuple 要素取得（`elements`/`elts` 差分吸収）を `CodeEmitter.tuple_elements()` へ移管。
   - [x] 「共通化候補一覧」を作り、`py2cpp.py` から段階的に移管する（`docs-jp/code-emitter-dispatch-plan.md` 参照）。
3. [x] Rust 固有処理の分離（最小雛形）
   - [x] `src/hooks/rs/` に Rust 用 hooks を追加。
   - [x] `src/profiles/rs/` に Rust 用 profile（syntax/runtime call map 等）を追加。
4. [ ] `py2rs.py` の EAST ベース再実装（段階的）。
   - [x] 最小版: EAST（`.py/.json`）読み込み→CodeEmitter経由で Rust 出力。
   - [x] 第2段: `test/fixtures/core` の基本ケースが通る範囲まで拡張（transpile 成功）。
   - [ ] 第3段: import / class / collections の変換品質を段階追加（出力品質・コンパイル互換を改善）。
   - [x] import 束縛を `use ...;` に変換（`meta.import_bindings` 優先）。
   - [x] `for (k, v) in dict.items()` 形の tuple ターゲットを生成。
   - [x] `dict[str, Any]` のような注釈でも、値側に具体型がある場合は宣言型を具体化。
   - [ ] class / Any / dict 連携の型整合（Rustコンパイル互換）を改善。
     - [x] Rust `Dict` 式で `entries` 形式を正しく展開し、要素脱落（`BTreeMap::from([])`）を修正。
     - [x] Rust `class` 出力に `#[derive(Clone, Debug)]` を付与し、`dict/items/clone` 経路のコンパイル互換を改善。
5. [ ] 検証と回帰テスト。
   - [x] `test/unit/` に py2rs 向け最小テストを追加（読み込み・文法・出力スモーク）。
   - [x] `tools/check_py2rs_transpile.py` を追加（fixtures/sample 一括トランスパイル確認）。
   - [x] `py2cpp.py` 側の既存挙動を壊していないことを回帰確認する（`tools/check_py2cpp_transpile.py`）。
6. [ ] 運用ルール（今回の指示反映）。
   - [x] 「py2rs と py2cpp の共通コードは CodeEmitter に移す」を実装ルールとして明文化する（`docs-jp/spec-dev.md`）。
   - [x] 途中で `py2rs.py` が壊れていても、段階コミット可（ただし方針違反は不可）。

## P4: 他言語トランスパイラの EAST 移行（py2rs の後）

- 着手条件: `P3`（py2rs の EAST 移行）が最小完了した後に着手する。
- 実施順: `py2js.py` → `py2cs.py` → `py2go.py` → `py2java.py` → `py2ts.py` → `py2swift.py` → `py2kotlin.py`
- 共通ルール: 各 `py2xx.py` は薄いCLIに限定し、共通ロジックは `CodeEmitter` へ寄せる。

1. [x] `py2js.py` を EAST ベースへ移行する。
   - [x] `src/common/` 依存を撤去する。
   - [x] JS 固有処理を hook/profile へ分離する。
   - [x] `browser` / `browser.widgets.dialog` を外部参照（ブラウザ環境）として解決する。
2. [x] `py2cs.py` を EAST ベースへ移行する。
   - [x] `src/common/` 依存を撤去する。
   - [x] C# 固有処理を hook/profile へ分離する（`src/hooks/cs/`, `src/profiles/cs/` 追加）。
   - [x] `test/unit/test_py2cs_smoke.py` / `tools/check_py2cs_transpile.py` を追加して回帰確認を自動化する。
3. [ ] `py2go.py` / `py2java.py` を EAST ベースへ移行する。
4. [ ] `py2ts.py` / `py2swift.py` / `py2kotlin.py` を EAST ベースへ移行する。
5. [ ] 言語横断の回帰テストを追加する。
   - [ ] 「EAST入力が同一なら、未対応時のエラー分類も各言語で同様」を確認するテストを追加する。

## 補足

- `Yanesdk` はブラウザ実行（Brython）前提のため、最終ゴールは `py2js` 側での実行互換。
- ただし現段階では `py2cpp.py` を通すことを前提に、frontend（EAST化）で落ちる箇所を先に解消する。
