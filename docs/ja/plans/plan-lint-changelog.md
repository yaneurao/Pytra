# 計画: emitter lint 変化点ログの自動記録 (P1-LINT-CHANGELOG)

## 背景

parity check の PASS 件数変化は `progress-preview/changelog.md` に自動記録されるようになったが、
emitter lint（ハードコード違反検出）の変化は記録されていない。
言語ごとの違反数・合格カテゴリ数が増減したタイミングを changelog に残し、改善・退行を追跡できるようにする。

## 設計

### 変化の検出タイミング

`check_emitter_hardcode_lint.py` が `emitter_lint.json` を書き出す直前に、
既存の `.parity-results/emitter_lint.json` を読み込んで旧値と比較する。

### 追記指標

- `pass_cats`（合格カテゴリ数）を "PASS 件数" に相当する指標として使用する
  - 増加 = 改善（violations が減った）
  - 減少 = 退行（violations が増えた）
- parity changelog と同じ `_append_parity_changelog` を再利用し、`case_root="lint"` で記録する

### フォーマット例

```markdown
| 2026-03-31T10:25 | rs | lint | 6→8 (+2) |  |
| 2026-03-31T10:25 | cs | lint | 6→4 (-2) | regression |
```

### 実装箇所

`check_emitter_hardcode_lint.py` の `_write_results()` 関数内、
`emitter_lint.json` を書き出す前後に追加する。

1. JSON 書き出し前に既存ファイルを読み込み、lang ごとの `pass_cats` を取得
2. JSON 書き出し後に `_append_parity_changelog` を lang ごとに呼び出す
3. `_append_parity_changelog` は `runtime_parity_check` から import して再利用する

### クールダウン・ロック

既存の `_append_parity_changelog` にロック・クールダウン（10分）が実装済みのため、
`case_root="lint"` で呼び出せばそのまま適用される。
marker ファイルは `.parity-results/.changelog_last_<lang>_lint` となる。

## 影響範囲

- `check_emitter_hardcode_lint.py` に import と前後比較ロジックを追加
- 既存の `runtime_parity_check.py` / `_append_parity_changelog` は変更不要
- `progress-preview/changelog.md` に lint 変化行が追加される

## 決定ログ

- 2026-03-31: 起票。pass_cats を指標として parity changelog 関数を再利用する方針に決定。
