# TODO（未完了）

<a href="../docs/todo.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-22

## 実行順（上から着手）

1. `P1-A: self_hosted parser / tokenizer 拡張（Yanesdk必須）`
2. `P0: Yanesdk（library + game）を py2cpp で通す最短経路`
3. `P1-B: import / module 解決（Yanesdk必須）`
4. `P2: 受け入れテスト追加（Yanesdk由来）`
5. `P3: py2rs（EAST移行）を CodeEmitter 中心で再設計`
6. `P4: 他言語トランスパイラの EAST 移行`

## Yanesdk 再調査メモ（2026-02-21）

- 調査対象: `Yanesdk/` 配下の `.py` 16ファイル（library 8 / game 7 / browser-shim 1）
- 現状結果: `py2cpp.py` 変換成功 `0/16`、失敗 `16/16`
- 役割別の初回失敗:
  - library（`*/yanesdk.py`）: `from ... import ... # type:ignore` が from-import 句として未対応（8/8）
  - game（`docs/*/*.py` のゲーム本体）: `from yanesdk import *`（BOM付き）が先頭で失敗（7/7）
  - browser-shim（`Yanesdk/yanesdk/browser.py`）: `class ...: pass` 未対応（1/1）
- 先頭ブロッカーを外した追加判明（代表ファイルで確認）:
  - 共通 parser/tokenizer 不足: `**`, `\` 継続行, class `pass`, トップレベル式文
  - library 側の追加不足: nested `def`（関数内関数）, `self. attr` 形式の属性参照
  - game 側の追加不足: Enum 風 `X = 0,`（末尾`,`付き代入）, nested `def`（例: `lifegame.py` 内 `def pset(...)`）
  - import 解決不足（最小プローブで確認）: `math` / `random` / `timeit` / `traceback` / `browser` が `missing_module`
- `;` について:
  - `Yanesdk` 側の文法誤りとして扱う。self_hosted parser では受理しない（サポート対象外）。
- `browser` / `browser.widgets.dialog` について:
  - Brython が提供する薄い wrapper であり、最終的には JavaScript 側の `document/window/canvas` などへ直接接続して動かす前提。
  - そのため `py2js` では「モジュール本体を変換する」のではなく「外部提供ランタイム（ブラウザ環境）への参照」として扱う方針にする。
- 正本ファイル運用:
  - `yanesdk.py` は `Yanesdk/yanesdk/yanesdk.py` を正本として扱う。
  - `Yanesdk/docs/*/yanesdk.py` は重複コピーとして扱い、解析・修正の基準にしない。

## P1-A: self_hosted parser / tokenizer 拡張（Yanesdk必須）

1. [x] UTF-8 BOM（`\ufeff`）を先頭トークンとして許容する。
2. [x] バックスラッシュ継続行（`\`）を字句解析で扱えるようにする。
3. [x] べき乗演算子 `**` の構文解析と EAST 生成を追加する。
4. [x] トップレベル式文（module body の `Expr`）を受理する。
5. [x] class body の `pass` を受理する。
6. [ ] `yield` / generator 構文を受理する（最小は `yield` 単体）。
7. [x] 関数内関数定義（nested `def`）を受理する。
8. [x] `obj. attr`（dot 前後に空白あり）を属性参照として受理する。
9. [x] class 内の末尾`,`付き代入（例: `X = 0,`）を tuple 代入として受理する（仕様固定）。
10. [x] 文末 `;` は受理しない（Yanesdk 側の文法誤りとして扱う）ことをエラー仕様へ明記する。

## P0: Yanesdk（library + game）を py2cpp で通す最短経路

1. [ ] `Yanesdk` 向けの前処理方針を確定する（Pytra本体対応 vs Yanesdk側の機械変換）。
   - [ ] `from yanesdk import *` の扱いを決める（Pytraでサポートするか、明示 import へ機械変換するか）。
   - [ ] `# type:ignore`（import行・def行末）の扱いを決める（tokenizerで無視するか、前処理で除去するか）。
2. [ ] `Yanesdk` を再利用するため、`docs/*/yanesdk.py` の重複配置を整理する（`Yanesdk/yanesdk/` への一本化）。
   - [ ] `py2cpp` 調査・smoke テストでは `Yanesdk/yanesdk/yanesdk.py` を常に優先する。
3. [ ] 成功条件を明文化する（少なくとも `library 1本 + game 7本` が `py2cpp.py` を通る）。

## P1-B: import / module 解決（Yanesdk必須）

1. [ ] `math` / `random` / `timeit` / `traceback` / `enum` / `typing` の取り扱い方針を統一する。
   - [ ] `pytra.std.*` へ寄せる移行ルールを定義する（自動変換 or ソース修正）。
2. [ ] `browser` / `browser.widgets.dialog` の扱いを backend 別に明確化する。
   - [ ] `py2js` では Brython/ブラウザ提供オブジェクトへの外部参照として解決する（モジュール変換対象にしない）。
   - [ ] `py2cpp` 調査時は `missing_module` を許容するか、検証用 shim を使うかを方針化する。

## P2: 受け入れテスト追加（Yanesdk由来）

1. [ ] 以下の最小 fixture を `test/fixtures/` に追加する。
   - [ ] BOM付き `from ... import ...`
   - [ ] `# type:ignore` 付き `from-import`
   - [ ] `**`
   - [ ] `\` 行継続
   - [ ] トップレベル式文
   - [ ] class body `pass`
   - [ ] `yield`
   - [ ] nested `def`
   - [ ] `obj. attr`
   - [ ] class 内 `X = 0,`
2. [ ] `tools/check_py2cpp_transpile.py` に Yanesdk 縮小ケース群を段階追加する。
3. [ ] `Yanesdk` 実ファイルを使った smoke テスト（library 1本 + game 1本）を追加する。

## P3: py2rs（EAST移行）を CodeEmitter 中心で再設計（Yanesdk対応後）

- 着手条件: 本セクションは `P0/P1-A/P1-B/P2` が完了するまで着手しない。
- 優先順: `Yanesdk` の構文サポートと import 解決を先に完了し、その後に `py2rs` へ着手する。

1. [ ] 方針固定: `py2rs.py` は「CLI + 入出力 + 依存解決」の薄いオーケストレータに限定する。
   - [ ] `py2rs.py` に Rust 固有の式/文変換ロジックを増やさない。
   - [ ] `src/common/` と `src/rs_module/` には依存しない。
2. [ ] `CodeEmitter` の責務拡張を先に実施する（py2rs実装より先）。
   - [ ] `py2cpp.py` と `py2rs.py` で共通化できる EAST ユーティリティ（型変換補助・import束縛・文/式ディスパッチ補助）を `src/pytra/compiler/east_parts/code_emitter.py` へ移す。
   - [ ] 「共通化候補一覧」を作り、`py2cpp.py` から段階的に移管する。
3. [ ] Rust 固有処理は hook/profile へ分離する。
   - [ ] `src/hooks/rs/` に Rust 用 hooks を追加し、言語固有分岐を hook で吸収する。
   - [ ] `src/profiles/rs/` に Rust 用 profile（syntax/runtime call map 等）を追加する。
4. [ ] `py2rs.py` の EAST ベース再実装（段階的）。
   - [ ] 最小版: EAST（`.py/.json`）読み込み→CodeEmitter経由で Rust 出力。
   - [ ] 第2段: `test/fixtures/core` の基本ケースが通る範囲まで拡張。
   - [ ] 第3段: import / class / collections などを段階追加。
5. [ ] 検証と回帰テスト。
   - [ ] `test/unit/` に py2rs 向け最小テストを追加（読み込み・文法・出力スモーク）。
   - [ ] `py2cpp.py` 側の既存挙動を壊していないことを回帰確認する。
6. [ ] 運用ルール（今回の指示反映）。
   - [ ] 「py2rs と py2cpp の共通コードは CodeEmitter に移す」を実装ルールとして明文化する。
   - [ ] 途中で `py2rs.py` が壊れていても、段階コミット可（ただし方針違反は不可）。

## P4: 他言語トランスパイラの EAST 移行（py2rs の後）

- 着手条件: `P3`（py2rs の EAST 移行）が最小完了した後に着手する。
- 実施順: `py2js.py` → `py2cs.py` → `py2go.py` → `py2java.py` → `py2ts.py` → `py2swift.py` → `py2kotlin.py`
- 共通ルール: 各 `py2xx.py` は薄いCLIに限定し、共通ロジックは `CodeEmitter` へ寄せる。

1. [ ] `py2js.py` を EAST ベースへ移行する。
   - [ ] `src/common/` 依存を撤去する。
   - [ ] JS 固有処理を hook/profile へ分離する。
2. [ ] `py2cs.py` を EAST ベースへ移行する。
   - [ ] `src/common/` 依存を撤去する。
   - [ ] C# 固有処理を hook/profile へ分離する。
3. [ ] `py2go.py` / `py2java.py` を EAST ベースへ移行する。
4. [ ] `py2ts.py` / `py2swift.py` / `py2kotlin.py` を EAST ベースへ移行する。
5. [ ] 言語横断の回帰テストを追加する。
   - [ ] 「EAST入力が同一なら、未対応時のエラー分類も各言語で同様」を確認するテストを追加する。

## 補足

- `Yanesdk` はブラウザ実行（Brython）前提のため、最終ゴールは `py2js` 側での実行互換。
- ただし現段階では `py2cpp.py` を通すことを前提に、frontend（EAST化）で落ちる箇所を先に解消する。
