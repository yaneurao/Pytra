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
- 2026-02-25: `runtime_parity_check` の基盤修正（`core.cpp`/`east_parts/core.py` の比較式分解の堅牢化、`tools/runtime_parity_check.py` の非C++向け `-o` 出力パス合わせ）を反映し、`math_extended` / `pathlib_extended` の `cpp` がPASSを確認。
- 2026-02-25: `src/pytra/std/sys.py` の標準入出力フォールバックを追加し、移植済みランタイムが未定義実装を要求した場合のCI/実行時クラッシュを抑制。
- 2026-02-25: 現時点で `swiftc` は未導入のため、`runtime_parity_check` では `swift` ターゲットがskip。`rs`/`cs`/`js`/`ts`/`go`/`java`/`kotlin` は出力生成とランタイム/インポート仕様の未整合により不一致・実行失敗。
- 追記用。
