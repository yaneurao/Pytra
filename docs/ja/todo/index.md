# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-14

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs/ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs/ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs/ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs/ja/todo/index.md` / `docs/ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。
- 一時出力は既存 `out/`（または必要時のみ `/tmp`）を使い、リポジトリ直下に新規一時フォルダを増やさない。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs/ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs/ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs/ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。

## 未完了タスク

### P0

- [ ] [ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01] relative wildcard import native backend rollout
  文脈: [p0-relative-wildcard-import-native-rollout.md](../plans/p0-relative-wildcard-import-native-rollout.md)
  進捗メモ: `S2-03` で `lua/php/ruby` も module-graph bundle transpile smoke を green にし、single-file direct lane は wildcard を fail-closed のまま維持した。次は coverage / parity docs を final state に同期する。

### P1

1. [ ] [ID: P1-NES3-NOT-IMPLEMENTED-ERROR-CPP-01] `NotImplementedError` を C++ lane で未定義シンボルにせず、`not_implemented_error.py` を compile まで通す。
文脈: [docs/ja/plans/p1-nes3-not-implemented-error-cpp-support.md](../plans/p1-nes3-not-implemented-error-cpp-support.md)
- 進捗メモ: 未着手。

2. [ ] [ID: P1-NES3-BYTES-MEMBER-TRUTHINESS-CPP-01] `bytes` member truthiness の `!bytes` residual を止め、`cartridge_like.py` を compile まで通す。
文脈: [docs/ja/plans/p1-nes3-bytes-member-truthiness-cpp-support.md](../plans/p1-nes3-bytes-member-truthiness-cpp-support.md)
- 進捗メモ: 未着手。

3. [ ] [ID: P1-NES3-LIST-DEFAULT-FACTORY-RC-LIST-CPP-01] `field(default_factory=lambda: [0] * N)` の `rc<list<T>>` lane を整合させ、`list_default_factory.py` を compile まで通す。
文脈: [docs/ja/plans/p1-nes3-list-default-factory-rc-list-cpp-support.md](../plans/p1-nes3-list-default-factory-rc-list-cpp-support.md)
- 進捗メモ: 未着手。

4. [ ] [ID: P1-NES3-PATH-ALIAS-PKG-CPP-01] `pytra.std.pathlib.Path` の別モジュール alias 再利用を C++ multi-file contract に揃え、`path_alias_pkg` を compile まで通す。
文脈: [docs/ja/plans/p1-nes3-path-alias-pkg-cpp-support.md](../plans/p1-nes3-path-alias-pkg-cpp-support.md)
- 進捗メモ: 未着手。

5. [ ] [ID: P1-NES3-APU-CONST-PKG-CPP-01] モジュール定数を使う imported class の C++ header 順序と参照 lane を揃え、`apu_const_pkg` を compile まで通す。
文脈: [docs/ja/plans/p1-nes3-apu-const-pkg-cpp-support.md](../plans/p1-nes3-apu-const-pkg-cpp-support.md)
- 進捗メモ: 未着手。

6. [ ] [ID: P1-NES3-BUS-PORT-PKG-CPP-01] import した bus 型の header/symbol qualification と受け渡し lane を揃え、`bus_port_pkg` を compile まで通す。
文脈: [docs/ja/plans/p1-nes3-bus-port-pkg-cpp-support.md](../plans/p1-nes3-bus-port-pkg-cpp-support.md)
- 進捗メモ: 未着手。

### P2

1. [ ] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01] 削除済み `src/runtime/cpp/core/**` compat surface を live tree の現役前提から完全に外し、guard-only 参照へ整理する。
文脈: [docs/ja/plans/p2-cpp-legacy-core-compat-retire.md](../plans/p2-cpp-legacy-core-compat-retire.md)
- 進捗メモ: 未着手。

2. [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01] 全言語の `@extern` runtime/emitter 契約を見直し、generated rewrite ではなく native owner + generic extern metadata に揃える。
文脈: [docs/ja/plans/p2-multilang-extern-runtime-realign.md](../plans/p2-multilang-extern-runtime-realign.md)
- 進捗メモ: 未着手。

3. [ ] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01] bundle-based coverage matrix を導入し、`feature x lane x backend` の contract coverage 100% を support matrix と分離して固定する。
文脈: [docs/ja/plans/p2-backend-contract-coverage-100.md](../plans/p2-backend-contract-coverage-100.md)
- 進捗メモ: 未着手。

4. [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01] `py_runtime.h` の typed fallback を EAST3 / C++ emitter / runtime SoT 側へ押し戻し、header を物理分割なしで縮める。
文脈: [docs/ja/plans/p2-cpp-pyruntime-upstream-fallback-shrink.md](../plans/p2-cpp-pyruntime-upstream-fallback-shrink.md)
- 進捗メモ: 未着手。
