# TODO（未完了）

<a href="../docs/todo.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-21

## Yanesdk 調査メモ（2026-02-21）

- 調査対象: `Yanesdk/` 配下の `.py` 16ファイル
- 現状結果: `py2cpp.py` 変換成功 `0/16`、失敗 `16/16`
- 初回失敗の主因（件数）:
  - `unsupported from-import clause: ... # type:ignore`（8件）
  - `from yanesdk import *`（7件、BOM付き行）
  - `class ...: pass`（1件）
- 既知ブロッカー除去後の追加判明:
  - `**`（べき乗）未対応
  - `\`（行継続）未対応
  - トップレベル式文（例: `TheApp()`）未対応
  - `yield`（generator）未対応
  - class内 `X = 0` 形式（非注釈の class 代入）は制約あり（Enum系以外で失敗）
  - import解決で `math` / `random` / `timeit` / `traceback` / `browser` が `missing_module`

## P0: Yanesdk を py2cpp で通す最短経路

1. [ ] `Yanesdk` 向けの前処理方針を確定する（Pytra本体対応 vs Yanesdk側の機械変換）。
   - [ ] `from yanesdk import *` の扱いを決める（Pytraでサポートするか、明示 import へ機械変換するか）。
   - [ ] `# type:ignore`（import行・def行末）の扱いを決める（tokenizerで無視するか、前処理で除去するか）。
2. [ ] `Yanesdk` を再利用するため、`docs/*/yanesdk.py` の重複配置を整理する（`Yanesdk/yanesdk/` への一本化）。

## P1: self_hosted parser / tokenizer 拡張（Yanesdk必須）

1. [ ] UTF-8 BOM（`\\ufeff`）を先頭トークンとして許容する。
2. [ ] バックスラッシュ継続行（`\\`）を字句解析で扱えるようにする。
3. [ ] べき乗演算子 `**` の構文解析と EAST 生成を追加する。
4. [ ] トップレベル式文（module body の `Expr`）を受理する。
5. [ ] class body の `pass` を受理する。
6. [ ] `yield` / generator 構文を受理する（最小は `yield` 単体）。

## P1: import / module 解決（Yanesdk必須）

1. [ ] `math` / `random` / `timeit` / `traceback` / `enum` / `typing` の取り扱い方針を統一する。
   - [ ] `pytra.std.*` へ寄せる移行ルールを定義する（自動変換 or ソース修正）。
2. [ ] `browser` / `browser.widgets.dialog` を Pytra のランタイムモジュールとして定義する。
   - [ ] 最低限 `Yanesdk/yanesdk/browser.py` 相当の API を import 解決できる形にする。

## P2: 受け入れテスト追加（Yanesdk由来）

1. [ ] 以下の最小 fixture を `test/fixtures/` に追加する。
   - [ ] BOM付き `from ... import ...`
   - [ ] `# type:ignore` 付き `from-import`
   - [ ] `**`
   - [ ] `\\` 行継続
   - [ ] トップレベル式文
   - [ ] class body `pass`
   - [ ] `yield`
2. [ ] `tools/check_py2cpp_transpile.py` に Yanesdk 縮小ケース群を段階追加する。

## 補足

- `Yanesdk` はブラウザ実行（Brython）前提のため、最終ゴールは `py2js` 側での実行互換。
- ただし現段階では `py2cpp.py` を通すことを前提に、frontend（EAST化）で落ちる箇所を先に解消する。
