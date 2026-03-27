<a href="../../en/plans/p3-future-annotations-removal.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P3: from __future__ import annotations の廃止検討

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P3-FUTURE-ANNOTATIONS-REMOVAL-01`

## 背景

`from __future__ import annotations` は Python 3.7+ でアノテーションの遅延評価を有効にする import。
Pytra のセルフホストパーサーはアノテーションを自前でパースしており、Python の評価タイミングに依存しない。

現状 `src/pytra/` 配下の複数ファイルでこの import が使われているが、
「Python 標準モジュールの import は一切認めない」ルールとの整合性がない。

## 方針

1. パーサーが `from __future__ import annotations` を no-op として無視する（現状対応済み）
2. `pytra.*` 配下のソースから `from __future__ import annotations` を削除しても transpile が通ることを確認
3. 問題なければ `from __future__ import annotations` を非推奨とし、将来的にエラー化

## 注意

- Python 3.10 以前では `from __future__ import annotations` がないと `X | Y` 型構文が使えない
- Pytra のターゲット Python バージョンが 3.12+ であれば不要
- Python 実行時にアノテーションが評価される箇所（dataclass の field 型等）では影響がある可能性

## 受け入れ基準

- `src/pytra/` 配下から `from __future__ import annotations` を削除しても transpile pass。
- Python 実行時にも問題ないことを確認。
- fixture / sample pass。

## 決定ログ

- 2026-03-19: pytra.* import 統一ルールとの整合性の観点で起票。Python 3.13 環境では不要の可能性が高い。
