<a href="../../en/language/backend-progress-selfhost.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# selfhost マトリクス

> 機械生成ファイル。`python3 tools/gen/gen_backend_progress.py` で更新する。
> 生成日時: 2026-03-30T05:21:19
> [凡例・関連リンク](./progress.md)

toolchain2 を各言語に変換し、変換後のコンパイラで全言語の emit ができるか。

| アイコン | 意味 |
|---|---|
| ⬜ | 未着手 |
| 🟨 | emit OK |
| 🟧 | build OK |
| 🟩 | parity PASS |

| selfhost 言語 \ emit 先 | cpp | go | rs | ts |
|---|---|---|---|---|
| Python (原本) | 🟩 | 🟩 | 🟨 | 🟨 |
| C++ selfhost | ⬜ | ⬜ | ⬜ | ⬜ |
| Go selfhost | ⬜ | ⬜ | ⬜ | ⬜ |
| Rust selfhost | ⬜ | ⬜ | ⬜ | ⬜ |
| TS selfhost | ⬜ | ⬜ | ⬜ | ⬜ |
