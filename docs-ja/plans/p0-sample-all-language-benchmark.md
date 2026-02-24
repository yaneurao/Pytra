# P0 サンプル実行基盤リカバリ

## 背景
`readme-ja.md` の実行速度表は長期的に「欠損値が多い」状態になっており、現在は次の 2 点が重なっています。
- C++ の比較対象コンパイルが失敗し、C++列が未計測
- Rust/C#/Go/Java/Swift/Kotlin の実行環境未導入のため未計測

本タスクでは、まず必要なツールチェインを整備して sample ベンチを全言語で再測定し、`readme-ja.md`（必要なら英語版）を更新する。

## 対応方針
- 0) 全言語実行に必要なチェインをこの環境で導入する（不足がある場合は代替運用・代替条件を明記）。
- 1) C++ の失敗原因をビルド実行で再確認し、失敗が再現しなくなるまで最小修正。
- 2) ベースライン更新可能条件（`tools/verify_sample_outputs.py`）に従ってベンチ計測。
- 3) サンプル実行時間表を `readme-ja.md` と `readme.md` に反映。

## 非対象
- sample 実装そのものの品質改善（出力美化、最適化）は別ID。
- README 文言の最終編集以外、既存リンク構造の変更は本タスク外。

## 受け入れ基準
- 指定した全言語（C++/Rust/C#/JS/TS/Go/Java/Swift/Kotlin）でベンチ測定または実行可否を明示。
- `readme-ja.md` の表に測定結果が反映され、欠損の説明が最新状態を反映している。
- 本タスク完了時に `docs-ja/todo/index.md` の進捗を 1 行更新。

## 決定ログ
- 2026-02-25: Swift toolchain を `swiftc` 実行可能環境として導入し、`/workspace/Pytra/.chain/swift/bin` から `swiftc/swift` を参照可能化（現時点は `runtime_parity_check` 実行時に PATH へ追加して使用）。
- 追記用。
