# P4: 全言語 selfhost 完全化（低低優先）

最終更新: 2026-02-27

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P4-MULTILANG-SH-01`

背景:
- 現状の multilang selfhost 状態では、C++ 以外に `stage1/stage2/stage3` の未達が残っている。
- `rs` は stage1 失敗、`cs`/`js` は stage2 失敗、`ts` は preview-only、`go/java/swift/kotlin` は multistage runner 未定義。
- 将来的に「全言語で自己変換チェーンが成立する」状態を作るため、低低優先で長期バックログ化する。

目的:
- `py2<lang>.py`（`cpp/rs/cs/js/ts/go/java/swift/kotlin`）の selfhost 成立条件を段階的に満たし、全言語で multistage 監視を通せる状態へ収束する。

対象:
- `tools/check_multilang_selfhost_stage1.py` / `tools/check_multilang_selfhost_multistage.py` / `tools/check_multilang_selfhost_suite.py`
- 各言語の `py2*.py` と対応 emitter/runtime
- selfhost 検証レポート（`docs-ja/plans/p1-multilang-selfhost-*.md`）の更新導線

非対象:
- 速度最適化やコードサイズ最適化
- backend 全面再設計（selfhost 成立に不要な大規模改修）
- 優先度 `P0` / `P1` / `P3` の既存タスクを追い越す着手

受け入れ基準:
- `tools/check_multilang_selfhost_suite.py` 実行結果で全言語が `stage1 pass` となる。
- multistage レポートで全言語が `stage2 pass` / `stage3 pass`（または明示的な恒久除外）になる。
- `runner_not_defined` / `preview_only` / `toolchain_missing` 依存の常態化が解消される。

確認コマンド:
- `python3 tools/check_multilang_selfhost_suite.py`
- `python3 tools/check_multilang_selfhost_stage1.py`
- `python3 tools/check_multilang_selfhost_multistage.py`
- `python3 tools/build_selfhost.py`

決定ログ:
- 2026-02-27: ユーザー要望により、全言語 selfhost 完全化を低低優先（P4）で TODO 追加する方針を確定した。

## 分解

- [ ] [ID: P4-MULTILANG-SH-01-S1-01] 現状の stage1/stage2/stage3 未達要因を言語別に固定化し、優先順（blocking chain）を明文化する。
- [ ] [ID: P4-MULTILANG-SH-01-S1-02] multistage runner 未定義言語（go/java/swift/kotlin）の runner 契約を定義し、`runner_not_defined` を解消する実装方針を確定する。
- [ ] [ID: P4-MULTILANG-SH-01-S2-01] Rust selfhost の stage1 失敗（from-import 受理）を解消し、stage2 へ進める。
- [ ] [ID: P4-MULTILANG-SH-01-S2-02] C# selfhost の stage2 compile 失敗を解消し、stage3 変換を通す。
- [ ] [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost の stage2 依存 transpile 失敗を解消し、multistage を通す。
- [ ] [ID: P4-MULTILANG-SH-01-S3-01] TypeScript の preview-only 状態を解消し、selfhost 実行可能な生成モードへ移行する。
- [ ] [ID: P4-MULTILANG-SH-01-S3-02] Go/Java/Swift/Kotlin の native backend 化タスクと接続し、selfhost 実行チェーンを有効化する。
- [ ] [ID: P4-MULTILANG-SH-01-S4-01] 全言語 multistage 回帰を CI 導線へ統合し、失敗カテゴリの再発を常時検知できるようにする。
- [ ] [ID: P4-MULTILANG-SH-01-S4-02] 完了判定テンプレート（各言語の stage 通過条件と除外条件）を文書化し、運用ルールを固定する。
