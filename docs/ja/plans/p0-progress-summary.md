<a href="../../en/plans/p0-progress-summary.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0-PROGRESS-SUMMARY: バックエンド全体サマリページを自動生成する

最終更新: 2026-03-30
ステータス: 完了（件数表示の修正が必要）

## 背景

各マトリクス（fixture / sample / stdlib / selfhost / emitter lint）が別ページに分かれており、全体像を把握するにはページを行き来する必要がある。1ページで全言語の状況を俯瞰できるサマリが必要。

## 設計

### サマリテーブル

各言語1行で、fixture / sample / stdlib / selfhost / emitter lint の状況を表示する。

```
| 言語 | fixture | sample | stdlib | selfhost | lint |
|---|---|---|---|---|---|
| C++ | 🟩 146/146 | 🟩 18/18 | 🟩 10/10 | ⬜ | 🟩 0 |
| Go | 🟩 147/147 | 🟩 18/18 | 🟩 10/10 | ⬜ | 🟥 27 |
| Rust | 🟥 100/146 | ⬜ | ⬜ | ⬜ | 🟥 6 |
| TS | 🟩 125/146 | 🟥 10/18 | ⬜ | ⬜ | 🟥 6 |
```

各セルの形式:
- fixture / sample / stdlib: `🟩 PASS件数/総件数` または `🟥 PASS件数/総件数` または `⬜`（未実行）
- selfhost: `🟩` / `🟥` / `⬜`（selfhost マトリクスの Python 行から取得）
- lint: `🟩 0`（違反なし）または `🟥 N`（違反 N 件）または `⬜`（emitter なし）

### 生成

`gen_backend_progress.py` が `_build_summary_matrix()` で生成。出力先:
- `docs/ja/progress/backend-progress-summary.md`
- `docs/en/progress/backend-progress-summary.md`

### 排他制御

parity check 末尾の自動再生成（`_maybe_regenerate_progress`, `_maybe_regenerate_benchmark`, `_maybe_refresh_selfhost_python`, `_maybe_run_emitter_lint`）は `.parity-results/.gen.lock` で排他制御する。lock が取れなければスキップ。

## 決定ログ

- 2026-03-30: サマリページの必要性を確認。fixture/sample/stdlib/selfhost/emitter lint を1ページに集約する方針に決定。
- 2026-03-30: 排他制御として `.parity-results/.gen.lock` を使う方針に決定。
- 2026-03-30: S1〜S4 完了。ただしサマリの各セルに `PASS件数/総件数`（例: `123/128`）が表示されていない。修正が必要。
