# TODO（未完了）

<a href="../docs/todo.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-21

## Yanesdk 再調査メモ（2026-02-21）

- 調査対象: `Yanesdk/` 配下の `.py` 16ファイル（library 8 / game 7 / browser-shim 1）
- 現状結果: `py2cpp.py` 変換成功 `0/16`、失敗 `16/16`
- 役割別の初回失敗:
  - library（`* /yanesdk.py`）: `from ... import ... # type:ignore` が from-import 句として未対応（8/8）
  - game（`docs/*/*.py` のゲーム本体）: `from yanesdk import *`（BOM付き）が先頭で失敗（7/7）
  - browser-shim（`Yanesdk/yanesdk/browser.py`）: `class ...: pass` 未対応（1/1）
- 先頭ブロッカーを外した追加判明（代表ファイルで確認）:
  - 共通 parser/tokenizer 不足: `**`, `\` 継続行, class `pass`, トップレベル式文
  - library 側の追加不足: nested `def`（関数内関数）, `;`, `self. attr` 形式の属性参照
  - game 側の追加不足: Enum 風 `X = 0,`（末尾`,`付き代入）, nested `def`（例: `lifegame.py` 内 `def pset(...)`）
  - import 解決不足（最小プローブで確認）: `math` / `random` / `timeit` / `traceback` / `browser` が `missing_module`
- `browser` / `browser.widgets.dialog` について:
  - Brython が提供する薄い wrapper であり、最終的には JavaScript 側の `document/window/canvas` などへ直接接続して動かす前提。
  - そのため `py2js` では「モジュール本体を変換する」のではなく「外部提供ランタイム（ブラウザ環境）への参照」として扱う方針にする。

## P0: Yanesdk（library + game）を py2cpp で通す最短経路

1. [ ] `Yanesdk` 向けの前処理方針を確定する（Pytra本体対応 vs Yanesdk側の機械変換）。
   - [ ] `from yanesdk import *` の扱いを決める（Pytraでサポートするか、明示 import へ機械変換するか）。
   - [ ] `# type:ignore`（import行・def行末）の扱いを決める（tokenizerで無視するか、前処理で除去するか）。
2. [ ] `Yanesdk` を再利用するため、`docs/*/yanesdk.py` の重複配置を整理する（`Yanesdk/yanesdk/` への一本化）。
3. [ ] 成功条件を明文化する（少なくとも `library 1本 + game 7本` が `py2cpp.py` を通る）。

## P1: self_hosted parser / tokenizer 拡張（Yanesdk必須）

1. [ ] UTF-8 BOM（`\\ufeff`）を先頭トークンとして許容する。
2. [ ] バックスラッシュ継続行（`\\`）を字句解析で扱えるようにする。
3. [ ] べき乗演算子 `**` の構文解析と EAST 生成を追加する。
4. [ ] トップレベル式文（module body の `Expr`）を受理する。
5. [ ] class body の `pass` を受理する。
6. [ ] `yield` / generator 構文を受理する（最小は `yield` 単体）。
7. [ ] 関数内関数定義（nested `def`）を受理する。
8. [ ] 文末 `;` を受理する（少なくとも無害トークンとして無視できるようにする）。
9. [ ] `obj. attr`（dot 前後に空白あり）を属性参照として受理する。
10. [ ] class 内の末尾`,`付き代入（例: `X = 0,`）の扱いを決める（tuple として受理 or 明示的に禁止エラー）。

## P1: import / module 解決（Yanesdk必須）

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
   - [ ] `\\` 行継続
   - [ ] トップレベル式文
   - [ ] class body `pass`
   - [ ] `yield`
   - [ ] nested `def`
   - [ ] 文末 `;`
   - [ ] `obj. attr`
   - [ ] class 内 `X = 0,`
2. [ ] `tools/check_py2cpp_transpile.py` に Yanesdk 縮小ケース群を段階追加する。
3. [ ] `Yanesdk` 実ファイルを使った smoke テスト（library 1本 + game 1本）を追加する。

## 補足

- `Yanesdk` はブラウザ実行（Brython）前提のため、最終ゴールは `py2js` 側での実行互換。
- ただし現段階では `py2cpp.py` を通すことを前提に、frontend（EAST化）で落ちる箇所を先に解消する。
