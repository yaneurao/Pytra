<a href="../../ja/plans/archive/20260309-p0-docs-tutorial-restructure-01.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260309-p0-docs-tutorial-restructure-01.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260309-p0-docs-tutorial-restructure-01.md`

# [ID: P0-DOCS-TUTORIAL-RESTRUCTURE-01] tutorial/ への導線再編

## 背景

- `docs/ja/how-to-use.md` に「初めて使う人向けの実行手順」と「開発運用メモ」と「高度な内部導線」が混在しており、入口として重い。
- すでに `advanced-usage.md` と `dev-operations.md` を切り出したが、docs 導線としてはまだ `how-to-use.md` が中心で、tutorial というまとまりが無い。
- 今後 `README` / `news` / `spec` から辿る正規入口を `docs/ja/tutorial/README.md` に寄せたい。

## 非対象

- `docs/en/` への翻訳反映
- `spec/` 文書の内容再設計
- tutorial 本文の大幅な新規執筆（今回は再配置と導線整理を優先）

## 受け入れ基準

- `docs/ja/tutorial/README.md` が新しい正規入口として存在する。
- 既存の `docs/ja/how-to-use.md` は削除せず、tutorial への案内 stub になる。
- いまの実行手順本文は `docs/ja/tutorial/how-to-use.md` へ移る。
- `advanced-usage.md` / `dev-operations.md` への導線が `tutorial/README.md` から辿れる。
- 代表的な docs 内リンク（少なくとも `README`, `docs/ja/README.md`, `docs/ja/how-to-use.md`）が新導線を指す。

## フェーズ

### S1. 現状棚卸し

- `how-to-use.md` を参照している docs を棚卸しする。
- tutorial 配下へどう分けるかを決める。

### S2. tutorial 入口の新設

- `docs/ja/tutorial/README.md` を追加する。
- `getting started`, `how-to-use`, `advanced-usage`, `dev-operations` への導線を整理する。

### S3. 本文移設

- `docs/ja/how-to-use.md` の本文を `docs/ja/tutorial/how-to-use.md` へ移す。
- 旧 `docs/ja/how-to-use.md` は薄い redirect/stub にする。

### S4. 参照更新

- `README.md`, `docs/ja/README.md`, 代表的な docs 内リンクを tutorial 入口基準へ更新する。
- broken link がないことを確認する。

### S5. 検証と archive

- `git diff --check`
- `rg` によるリンク棚卸し
- 必要なら簡易リンク確認

## 分解

- [x] `P0-DOCS-TUTORIAL-RESTRUCTURE-01-S1-01` 参照元と再配置方針を棚卸しする
- [x] `P0-DOCS-TUTORIAL-RESTRUCTURE-01-S2-01` `docs/ja/tutorial/README.md` を新設する
- [x] `P0-DOCS-TUTORIAL-RESTRUCTURE-01-S3-01` 実行手順本文を `docs/ja/tutorial/how-to-use.md` へ移す
- [x] `P0-DOCS-TUTORIAL-RESTRUCTURE-01-S3-02` 旧 `docs/ja/how-to-use.md` を redirect/stub 化する
- [x] `P0-DOCS-TUTORIAL-RESTRUCTURE-01-S4-01` 代表 docs のリンクを tutorial 入口へ更新する
- [x] `P0-DOCS-TUTORIAL-RESTRUCTURE-01-S5-01` 検証して archive する

## 決定ログ

- 2026-03-09: tutorial/ を新設し、`how-to-use.md` を tutorial 本文へ移したうえで旧 path は互換 stub として残す方針を採る。
- 2026-03-09: `docs/ja/tutorial/README.md` を新しい入口として追加し、`docs/ja/tutorial/how-to-use.md` へ実行手順本文を移した。旧 `docs/ja/how-to-use.md` は redirect/stub として残した。
- 2026-03-09: live docs の参照は `README.md`, `docs/ja/README.md`, `docs/ja/index.md`, `spec-user.md`, `spec-tools.md`, `spec-options.md`, `spec-codex.md`, `advanced-usage.md`, `dev-operations.md` を tutorial 導線へ更新し、archive / 旧計画書内の履歴参照はそのまま維持した。
