<a href="../../en/progress/backend-progress-summary.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# バックエンド全体サマリ

> 機械生成ファイル。`python3 tools/gen/gen_backend_progress.py` で更新する。
> 生成日時: 2026-04-02T13:46:20
> [関連リンク](./index.md)

各言語の fixture / sample / stdlib / selfhost / emitter lint の状況を一覧表示する。

| アイコン | 意味 |
|---|---|
| 🟩 | PASS |
| 🟥 | FAIL（1件以上） |
| ⬜ | 未実行 |

| | cpp | rs | cs | ps1 | js | ts | dart | go | java | scala | kotlin | swift | ruby | lua | php | nim | julia | zig |
|---| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **fixture** | 🟥<br>139/140 | 🟥<br>131/140 | 🟥<br>138/140 | ⬜<br>&nbsp; | 🟥<br>138/140 | 🟥<br>138/140 | ⬜<br>&nbsp; | 🟥<br>127/140 | 🟥<br>138/140 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | 🟥<br>138/140 | 🟩<br>140/140 | 🟩<br>140/140 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; |
| **sample** | 🟩<br>18/18 | 🟩<br>18/18 | 🟩<br>18/18 | ⬜<br>&nbsp; | 🟩<br>18/18 | 🟩<br>18/18 | ⬜<br>&nbsp; | 🟩<br>18/18 | 🟩<br>18/18 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | 🟩<br>18/18 | 🟥<br>2/18 | 🟥<br>1/18 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; |
| **stdlib** | 🟩<br>16/16 | 🟩<br>16/16 | 🟩<br>16/16 | ⬜<br>&nbsp; | 🟩<br>16/16 | 🟩<br>16/16 | ⬜<br>&nbsp; | 🟩<br>16/16 | 🟩<br>16/16 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | 🟩<br>16/16 | 🟩<br>16/16 | 🟥<br>14/16 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; |
| **selfhost** | 🟥<br>0/19 | 🟨<br>1/19 | 🟨<br>1/19 | ⬜<br>&nbsp; | 🟨<br>1/19 | 🟨<br>1/19 | ⬜<br>&nbsp; | 🟥<br>0/19 | 🟨<br>1/19 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | 🟨<br>1/19 | 🟥<br>0/19 | 🟥<br>0/19 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; |
| **emitter lint** | 🟩<br>8/8 | 🟥<br>6/8 | 🟩<br>8/8 | ⬜<br>&nbsp; | 🟩<br>8/8 | 🟩<br>8/8 | ⬜<br>&nbsp; | 🟥<br>7/8 | 🟩<br>8/8 | ⬜<br>&nbsp; | ⬜<br>&nbsp; | ⬜<br>&nbsp; | 🟩<br>8/8 | 🟩<br>8/8 | 🟩<br>8/8 | 🟥<br>5/8 | ⬜<br>&nbsp; | ⬜<br>&nbsp; |
