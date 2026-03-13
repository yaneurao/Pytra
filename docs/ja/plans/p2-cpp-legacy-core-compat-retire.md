# P2: 削除済み `src/runtime/cpp/core/**` compat surface の残滓を retire する

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01`

背景:
- 現行の C++ runtime ownership は `src/runtime/cpp/native/core/` と `src/runtime/cpp/generated/core/` に分離されており、`src/runtime/cpp/core/` 自体は既に存在しない。
- それでも live tree には、削除済み `src/runtime/cpp/core/**` を現役 surface と誤認しやすい残滓がまだ残っている。
- 代表例として [docs/ja/plans/p0-runtime-root-reset-cpp-parity.md](./p0-runtime-root-reset-cpp-parity.md) は完了済みなのに `src/runtime/cpp/core` + `src/runtime/cpp/gen` を canonical layout として記述している。
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

- [ ] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S1-01] live tree に残る `src/runtime/cpp/core/**` 参照を棚卸しし、正の参照と guard-only 参照へ分類する。
- [ ] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S2-01] stale-complete plan や旧 layout を canonical と書いている live docs を archive / cleanup する。
- [ ] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S2-02] tooling / test の `src/runtime/cpp/core/**` 言及を guard-only wording へ正規化し、誤解しやすい表現を除去する。
- [ ] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S3-01] checker / unit test / docs mirror を current ownership contract に同期して task を閉じる。

決定ログ:
- 2026-03-13: `src/runtime/cpp/core/` は既に削除済みであることを前提に、残滓整理だけを追う closeout task として起票した。
