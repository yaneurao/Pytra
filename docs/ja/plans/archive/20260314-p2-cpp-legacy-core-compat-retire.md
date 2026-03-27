<a href="../../../en/plans/archive/20260314-p2-cpp-legacy-core-compat-retire.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: 削除済み `src/runtime/cpp/core/**` compat surface の残滓を retire する

最終更新: 2026-03-14

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01`

背景:
- 現行の C++ runtime ownership は `src/runtime/cpp/native/core/` と `src/runtime/cpp/generated/core/` に分離されており、`src/runtime/cpp/core/` 自体は既に存在しない。
- それでも live tree には、削除済み `src/runtime/cpp/core/**` を現役 surface と誤認しやすい残滓がまだ残っている。
- 代表例だった [docs/ja/plans/archive/20260306-p0-runtime-root-reset-cpp-parity.md](./archive/20260306-p0-runtime-root-reset-cpp-parity.md) は完了済み plan なのに live `plans/` に残り、`src/runtime/cpp/core` + `src/runtime/cpp/gen` を canonical layout として記述していた。
- 一方で `tools/check_runtime_cpp_layout.py` や `test_runtime_symbol_index.py` のように、legacy `src/runtime/cpp/core/**` の再出現を fail-fast に検知する負の guard は現役 contract として必要である。

目的:
- 削除済み `src/runtime/cpp/core/**` を live docs / tooling / tests の「現役 layout 前提」から完全に外す。
- legacy path への言及は「再出現禁止を監視する guard-only 参照」に限定し、誤読しにくい形へ整理する。

対象:
- live plan / spec / tooling / tests に残る `src/runtime/cpp/core/**` の正の参照棚卸し
- stale-complete な live plan の archive / wording cleanup
- guard-only 参照として残すべき `src/runtime/cpp/core/**` 言及の分類と wording 正規化
- TODO / plan / English mirror の同期

非対象:
- `src/runtime/cpp/native/core/**` / `generated/core/**` の ownership redesign
- `runtime2` 退避 tree の全面整理
- C++ runtime 実装そのものの機能変更

受け入れ基準:
- live tree に `src/runtime/cpp/core/**` を canonical / present surface と記述する箇所が残らない。
- legacy `src/runtime/cpp/core/**` 参照は、再出現禁止の guard / negative assertion として必要な箇所だけに限定される。
- stale-complete plan が active live plan と誤認されない状態に整理される。
- related checker / unit test / docs wording が current ownership contract に同期する。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `rg -n "src/runtime/cpp/core|runtime/cpp/core/" src tools test docs -g '!**/archive/**'`
- `python3 tools/check_runtime_cpp_layout.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_runtime_cpp_layout.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_runtime_symbol_index.py'`
- `git diff --check`

## 分解

- [x] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S1-01] live tree に残る `src/runtime/cpp/core/**` 参照を棚卸しし、正の参照と guard-only 参照へ分類した。
- [x] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S2-01] stale-complete plan や旧 layout を canonical と書いている live docs を archive / cleanup した。
- [x] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S2-02] tooling / test の `src/runtime/cpp/core/**` 言及を guard-only wording として再確認し、誤解しやすい表現を除去した。
- [x] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S3-01] checker / unit test / docs mirror を current ownership contract に同期して task を閉じた。

決定ログ:
- 2026-03-13: `src/runtime/cpp/core/` は既に削除済みであることを前提に、残滓整理だけを追う closeout task として起票した。
- 2026-03-14: live tree の正の参照は stale-complete `p0-runtime-root-reset-cpp-parity.md` に集約されていることを確認し、同 plan を `docs/ja/plans/archive/20260306-p0-runtime-root-reset-cpp-parity.md` へ移して `todo/archive/20260306.md` と archive index の文脈リンクを archive 先へ更新した。
- 2026-03-14: checked-in `test/transpile/cpp/**` snapshot に残っていた `runtime/cpp/core/**` include/source path も `runtime/cpp/native/core/**` へ正規化し、legacy path の positive fixture 残滓を除去した。
- 2026-03-14: `rg -n "src/runtime/cpp/core|runtime/cpp/core/" src tools test docs -g '!**/archive/**'` の残件は `check_runtime_cpp_layout.py` / `check_runtime_core_gen_markers.py` / runtime spec 群 / negative assertion test の guard-only wording に限定されていることを確認した。
