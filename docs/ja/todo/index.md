# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-13

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
- [ ] [ID: P0-RAW-EAST3-NODE-SHAPE-VALIDATOR-01] raw EAST3 validator の node-shape 誤判定を解消し、auxiliary map の `meta` / `kind` key で false positive を出さない。文脈: [p0-raw-east3-node-shape-validator.md](../plans/p0-raw-east3-node-shape-validator.md)
- [x] [ID: P0-RAW-EAST3-NODE-SHAPE-VALIDATOR-01-S1-01] `any_dict_items` / `18_mini_language_interpreter` と synthetic auxiliary-map case を regression test と plan に固定した。
- [x] [ID: P0-RAW-EAST3-NODE-SHAPE-VALIDATOR-01-S2-01] raw EAST3 validator を node-shaped dict 限定へ狭め、actual node fail-closed を維持した。
- [ ] [ID: P0-RAW-EAST3-NODE-SHAPE-VALIDATOR-01-S2-02] targeted backend transpile verification と TODO/decision log を同期し、matrix 上の validator-origin failure を close state へ寄せる。

### P0: Pytra-NES representative C++ mini repro contract

- [ ] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01] Pytra-NES の representative な multi-file package（括弧付き sibling relative import + `dataclass` + `deque[float]` field + `deque` method）を C++ representative lane で build/run まで固定する。
  - 文脈: [docs/ja/plans/p0-pytra-nes-cpp-mini-repro-contract.md](../plans/p0-pytra-nes-cpp-mini-repro-contract.md)
- [x] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01-S1-01] representative package smoke を追加し、`from .controller import (...)` と `timestamps: deque[float] = field(init=False, repr=False)` を併用する C++ multi-file build/run baseline を固定した。
  - 進捗メモ: `controller.py` / `pad_state.py` / `ppu.py` の 3 module package を `test_py2cpp_features.py` に追加し、`pad_state.h` へ `::std::deque<float64>` が出て `field(...)` が漏れず、実行結果が `3 / 1.5 / 1` になることを smoke 化した。
- [ ] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01-S2-01] smoke で露出した generated include / class layout / method lowering の drift を source guard 化し、Pytra-NES representative lane の regression を fail-fast にする。
- [ ] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01-S3-01] TODO / plan / support docs を representative Pytra-NES mini repro contract に同期し、close する。
