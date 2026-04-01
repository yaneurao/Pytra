<a href="../../en/progress/backend-progress-summary.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# バックエンド全体サマリ

> 機械生成ファイル。`python3 tools/gen/gen_backend_progress.py` で更新する。
> 生成日時: 2026-04-01T12:05:09
> [関連リンク](./index.md)

各言語の fixture / sample / stdlib / selfhost / emitter lint の状況を一覧表示する。

| アイコン | 意味 |
|---|---|
| 🟩 | PASS |
| 🟥 | FAIL（1件以上） |
| ⬜ | 未実行 |

| | cpp | rs | cs | ps1 | js | ts | dart | go | java | swift | kotlin | ruby | lua | scala | php | nim | julia | zig |
|---| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **fixture** | 🟥<br>134/137 | 🟥<br>135/137 | 🟥<br>136/137 | ⬜<br>&nbsp; | 🟥<br>136/137 | 🟥<br>136/137 | ⬜<br>&nbsp; | 🟥<br>131/137 | 🟩<br>137/137 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | 🟥<br>112/137 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; |
| **sample** | 🟩<br>18/18 | 🟩<br>18/18 | 🟩<br>18/18 | ⬜<br>&nbsp; | 🟩<br>18/18 | 🟩<br>18/18 | ⬜<br>&nbsp; | 🟩<br>18/18 | 🟩<br>18/18 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | 🟥<br>1/18 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; |
| **stdlib** | 🟩<br>16/16 | 🟩<br>16/16 | 🟩<br>16/16 | ⬜<br>&nbsp; | 🟩<br>16/16 | 🟩<br>16/16 | ⬜<br>&nbsp; | 🟩<br>16/16 | 🟩<br>16/16 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | 🟩<br>16/16 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; |
| **selfhost** | 🟥<br>0/19 | 🟥<br>0/19 | 🟥<br>1/19 | ⬜<br>&nbsp; | 🟥<br>0/19 | 🟥<br>1/19 | ⬜<br>&nbsp; | 🟥<br>0/19 | 🟥<br>1/19 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | 🟥<br>0/19 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; |
| **emitter lint** | 🟥<br>7/9 | 🟥<br>6/9 | 🟥<br>8/9 | ⬜<br>&nbsp; | 🟥<br>7/9 | 🟥<br>7/9 | 🟩<br>1/9 | 🟥<br>7/9 | 🟩<br>9/9 | 🟩<br>1/9 | 🟩<br>1/9 | 🟥<br>5/9 | 🟥<br>7/9 | 🟩<br>1/9 | 🟥<br>7/9 | 🟥<br>6/9 | 🟩<br>1/9 | 🟩<br>1/9 |
