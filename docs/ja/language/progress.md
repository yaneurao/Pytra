<a href="../../en/language/progress.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# プロジェクト進捗

## バックエンドサポート状況

| fixture parity | sample parity | selfhost |
|---|---|---|
| [fixture マトリクス](./backend-progress-fixture.md) | [sample マトリクス](./backend-progress-sample.md) | [selfhost マトリクス](./backend-progress-selfhost.md) |

### アイコン凡例

| アイコン | 意味 |
|---|---|
| 🟩 | PASS（emit + compile + run + stdout 一致） |
| 🟥 | FAIL（transpile_failed / run_failed / output_mismatch 等） |
| 🟨 | TM（toolchain_missing）/ emit OK（selfhost） |
| 🟪 | TO（timeout） |
| 🟧 | build OK（selfhost） |
| ⬜ | 未実行 / 未着手 |
| ⚠ | 結果が 7 日以上古い |

> fixture / sample / selfhost の各マトリクスは `python3 tools/gen/gen_backend_progress.py` で機械生成される。

## タスク一覧

[TODO 索引](../todo/index.md) — 領域別（C++ / Go / Rust / TS / インフラ）のタスク管理。

## 更新履歴

[![更新履歴](https://img.shields.io/badge/📋_更新履歴-全履歴を見る-2563EB?style=for-the-badge)](../changelog.md)

## ドキュメント

- [チュートリアル](../tutorial/README.md)
- [ガイド](../guide/README.md)
- [仕様書](../spec/index.md)
