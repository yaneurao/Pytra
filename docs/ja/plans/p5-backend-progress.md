<a href="../../en/plans/p5-backend-progress.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P5-BACKEND-PROGRESS: parity 結果の自動蓄積 + 進捗ページ自動生成

最終更新: 2026-03-30
ステータス: 完了

## 背景

Pytra は C++/Go/Rust/TS の 4 backend を並行開発しており、各 backend の fixture parity / sample parity / selfhost の進捗を把握する手段がない。parity check は数時間かかるため頻繁に全件回せず、部分実行の結果が蓄積されないまま失われている。

外部から見て「プロジェクトが活発に進んでいるか」を判断できる進捗ページがほしい。

## 設計

### 1. 結果の自動蓄積

`runtime_parity_check.py` / `runtime_parity_check_fast.py` が実行終了時に `work/parity-results/` へ結果を無条件で書き出す。

- ファイル: `work/parity-results/<target>_<case-root>.json`（例: `go_fixture.json`, `cpp_sample.json`）
- 既存ファイルがあればケース単位でマージ（上書きではなく更新）
- 各ケースにタイムスタンプを付与
- `--summary-json` は追加の出力先として残す（互換性）

JSON 形式:

```json
{
  "target": "go",
  "case_root": "fixture",
  "results": {
    "add": {
      "category": "ok",
      "timestamp": "2026-03-29T14:23:01"
    },
    "class": {
      "category": "ok",
      "timestamp": "2026-03-29T14:23:05"
    },
    "pytra_runtime_png": {
      "category": "run_failed",
      "detail": "out/ directory missing",
      "timestamp": "2026-03-28T10:15:30"
    }
  }
}
```

- `--category oop` で部分実行した場合、oop のケースだけ timestamp が更新され、他カテゴリの結果はそのまま残る
- fixture を新規追加した場合、JSON にエントリがないだけ。集計時に「未実行」として検出される
- `work/` は `.gitignore` 対象なので結果ファイル自体はコミットしない

### 2. selfhost 結果

selfhost は parity check とは別の導線（`pytra-cli2 -build`、`g++`、`go build`、`cargo build`、`tsc`）で実行される。結果は `work/parity-results/selfhost_<lang>.json` に記録する。

JSON 形式:

```json
{
  "selfhost_lang": "go",
  "stages": {
    "emit": {"status": "ok", "timestamp": "2026-03-29T15:00:00"},
    "build": {"status": "fail", "detail": "3 compile errors", "timestamp": "2026-03-29T15:01:00"},
    "parity": {"status": "not_reached", "timestamp": ""}
  },
  "emit_targets": {
    "cpp": {"status": "ok", "timestamp": "2026-03-29T15:00:10"},
    "go": {"status": "ok", "timestamp": "2026-03-29T15:00:20"},
    "rs": {"status": "not_tested", "timestamp": ""},
    "ts": {"status": "not_tested", "timestamp": ""}
  }
}
```

### 3. 進捗ページ生成

`tools/gen/gen_backend_progress.py` が `work/parity-results/*.json` を読み、fixture 一覧・sample 一覧と突き合わせて Markdown を生成する。

出力先（日英同時生成。機械生成物を手動翻訳するのは非効率なため、スクリプトが両言語を直接出力する）:

- `docs/ja/progress/backend-progress.md` — クッションページ（凡例 + 3マトリクスへのリンク + 関連リンク）。手書き。
- `docs/ja/progress/backend-progress-fixture.md` — fixture parity マトリクス。機械生成。
- `docs/ja/progress/backend-progress-sample.md` — sample parity マトリクス。機械生成。
- `docs/ja/progress/backend-progress-selfhost.md` — selfhost マトリクス。機械生成。
- `docs/en/progress/` にも同じ 4 ファイルを生成（クッションページの見出しだけ英語）。

#### fixture parity マトリクス

全ケース × 全言語の表。状態アイコン:

| アイコン | 意味 |
|---|---|
| 🟩 | PASS（emit + compile + run + stdout 一致） |
| 🟥 | FAIL（transpile_failed / run_failed / output_mismatch） |
| 🟨 | TM（toolchain_missing） |
| 🟪 | TO（timeout） |
| ⬜ | 未実行 |

```
| カテゴリ | ケース | C++ | Go | Rust | TS |
|---|---|---|---|---|---|
| core | add | 🟩 | 🟩 | 🟩 | 🟩 |
| core | fib | 🟩 | 🟩 | 🟥 | ⬜ |
| oop | class | 🟩 | 🟩 | 🟩 | 🟩 |
| ... | ... | ... | ... | ... | ... |
| | **合計** | 🟩115 🟥31 | 🟩146 | 🟩80 🟥20 ⬜46 | 🟩50 ⬜96 |
```

#### sample parity マトリクス

sample 18 件 × 全言語。fixture と同じ形式。

#### selfhost マトリクス

selfhost 言語 × emit 先言語の表。段階的な進捗を表示。

| アイコン | 意味 |
|---|---|
| ⬜ | 未着手 |
| 🟨 | emit OK |
| 🟧 | build OK |
| 🟩 | parity PASS |

```
| selfhost 言語 \ emit 先 | C++ | Go | Rust | TS |
|---|---|---|---|---|
| Python (原本) | 🟩 | 🟩 | 🟨 | 🟨 |
| C++ selfhost | ⬜ | ⬜ | ⬜ | ⬜ |
| Go selfhost | ⬜ | ⬜ | ⬜ | ⬜ |
| Rust selfhost | ⬜ | ⬜ | ⬜ | ⬜ |
| TS selfhost | ⬜ | ⬜ | ⬜ | ⬜ |
```

最終目標は全マスが 🟩。

#### 鮮度警告

タイムスタンプが 7 日以上前のケースには ⚠ を付与し、再実行を促す。

### 4. README からのリンク

README.md の Changelog セクションの上あたりに進捗ページへのリンクを追加する。

```markdown
## Backend Progress

[fixture / sample / selfhost の進捗マトリクス](docs/ja/progress/backend-progress.md)
```

## 運用フロー

1. 各担当が parity check を回す（部分実行 OK）
2. 結果が `work/parity-results/` に自動蓄積される
3. 任意のタイミングで `python3 tools/gen/gen_backend_progress.py` を実行
4. `docs/ja/progress/backend-progress.md` が更新される
5. コミット・プッシュ

## 決定ログ

- 2026-03-29: parity check の結果を所定フォルダに自動蓄積し、集計スクリプトで進捗ページを生成する方針に決定。`--summary-json` のオプション指定忘れを防ぐため、スクリプト内で無条件に書き出す。
- 2026-03-29: 部分実行（`--category oop` 等）の結果もマージで蓄積する方針。fixture 追加時は JSON にエントリがないだけで、集計時に「未実行」として検出される。
- 2026-03-29: selfhost マトリクスは「selfhost 言語 × emit 先言語」のクロス表。全言語で全言語の selfhost ができるのが最終目標。
- 2026-03-30: P5-PROGRESS S1〜S4 完了。`_save_parity_results()` を runtime_parity_check.py に実装し fast 版からも再利用。`tools/gen/gen_backend_progress.py` で日英進捗ページを生成。README.md にリンク追加。selfhost 形式は計画書の定義通りで gen_backend_progress.py が selfhost_<lang>.json を読んでマトリクス表示する形で実装済み。
