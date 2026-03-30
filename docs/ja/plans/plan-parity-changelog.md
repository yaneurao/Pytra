# 計画: parity 変化点ログの自動記録 (P0-PARITY-CHANGELOG)

## 背景

parity check の結果が退行しても、progress matrix からは気づけない。PASS 件数が変化したタイミングで自動的にログを記録し、いつ何が変わったかを追跡できるようにする。

## 設計

### 出力先

`docs/{ja,en}/progress-preview/changelog.md` に追記する。

- `progress-preview/` は git 管理外（自動生成物）
- 週1程度で `progress/` に手動コピーされ、その時点で git に入る
- changelog も一緒にコピーされるので、履歴が git に残る

### フォーマット

```markdown
# Parity Changelog

| 日時 | 言語 | case-root | 変化 | 備考 |
|---|---|---|---|---|
| 2026-03-31T10:15 | cpp | fixture | 126→131 (+5) | |
| 2026-03-31T08:45 | rs | fixture | 81→0 (-81) | regression |
```

- 新しい行が上に来るよう、テーブルヘッダの直後に挿入する
- 変化がない場合は何も追記しない
- 減少時は備考に `regression` と明記

### 記録タイミング

`runtime_parity_check_fast.py` が `.parity-results/` に結果を保存するタイミングで:

1. 既存の `.parity-results/<target>_<case-root>.json` から前回の PASS 件数を取得
2. 今回の PASS 件数と比較
3. 変化があれば `progress-preview/changelog.md` に行を追記

### 実装箇所

`runtime_parity_check_fast.py` の `_save_parity_results()` 呼び出し付近。既存の JSON を読んで PASS 件数を数え、新しい結果と比較するだけ。

## 影響範囲

- `runtime_parity_check_fast.py` に changelog 追記ロジックを追加
- `runtime_parity_check.py`（非 fast 版）にも同様に追加
- `progress-preview/changelog.md` が新規ファイルとして生成される
- 既存の parity check の動作には影響なし（追記のみ）
