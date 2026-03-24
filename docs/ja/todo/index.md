# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-24（パイプライン再設計着手に伴い全 TODO をアーカイブへ移動）

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

### 共通

文脈: [docs/ja/plans/plan-pipeline-redesign.md](../plans/plan-pipeline-redesign.md)
コーディング規約: plan §5（Any/object 禁止、pytra.std 再実装禁止、グローバル可変状態禁止 等）

1. [x] [ID: P0-PIPELINE-V2-S0] golden file 生成ツール (`tools/generate_golden.py`) — 完了

### P0-PARSE: py → east1 (Agent A)

作業ディレクトリ: `toolchain2/parse/py/`
入力: `test/fixture/source/py/*.py`, `sample/py/*.py`
正解: `test/fixture/east1/py/`, `test/sample/east1/py/`

1. [ ] [ID: P0-PARSE-S1] 自前パーサーで fixture 132 件の .py.east1 が golden と一致する
2. [ ] [ID: P0-PARSE-S2] sample 18 件の .py.east1 が golden と一致する
3. [ ] [ID: P0-PARSE-S3] `pytra-cli2 -parse` を toolchain2 の自前パーサーに切り替える

### P0-RESOLVE: east1 → east2 (Agent B)

作業ディレクトリ: `toolchain2/resolve/py/`
入力: `test/fixture/east1/py/*.py.east1`, `test/sample/east1/py/*.py.east1`
正解: `test/fixture/east2/`, `test/sample/east2/`

1. [x] [ID: P0-RESOLVE-S1] cross-module 型解決を実装し、fixture 132 件の .east2 が golden と一致する — 完了
2. [x] [ID: P0-RESOLVE-S2] sample 18 件の .east2 が golden と一致する（signature_registry のハードコードなし） — 完了
3. [x] [ID: P0-RESOLVE-S3] `pytra-cli2 -resolve` を実装する — 完了

### P0-COMPILE: east2 → east3 (Agent C)

作業ディレクトリ: `toolchain2/compile/`
入力: `test/fixture/east2/*.east2`, `test/sample/east2/*.east2`
正解: `test/fixture/east3/`, `test/sample/east3/`

1. [ ] [ID: P0-COMPILE-S1] core lowering を実装し、fixture 132 件の .east3 が golden と一致する
2. [ ] [ID: P0-COMPILE-S2] sample 18 件の .east3 が golden と一致する
3. [ ] [ID: P0-COMPILE-S3] `pytra-cli2 -compile` を実装する

### P0-OPTIMIZE: east3 最適化 (Agent D)

作業ディレクトリ: `toolchain2/optimize/`
入力: `test/fixture/east3/*.east3`, `test/sample/east3/*.east3`
正解: `test/fixture/east3-opt/`, `test/sample/east3-opt/`

1. [ ] [ID: P0-OPTIMIZE-S1] whole-program 最適化を実装し、fixture 132 件の .east3 が golden と一致する
2. [ ] [ID: P0-OPTIMIZE-S2] sample 18 件の .east3 が golden と一致する
3. [ ] [ID: P0-OPTIMIZE-S3] `pytra-cli2 -optimize` を実装する

### P0-EMIT: east3 → target (Agent E 以降)

作業ディレクトリ: `toolchain2/emit/cpp/` 等
入力: `test/fixture/east3-opt/*.east3`, `test/sample/east3-opt/*.east3`
正解: fixture は `test/fixture/emit/*.txt`、sample は `sample/golden/manifest.json`

1. [ ] [ID: P0-EMIT-S1] C++ emit を実装し、fixture の parity テストが通る
2. [ ] [ID: P0-EMIT-S2] sample 18 件の parity テストが通る
3. [ ] [ID: P0-EMIT-S3] `pytra-cli2 -emit --target=cpp` を実装する

### P0-BUILD: 一括実行

1. [ ] [ID: P0-BUILD-S1] `pytra-cli2 -build --target=cpp` で全 18 sample が compile + run できる

注: 旧 TODO は [2026-03-24 アーカイブ](archive/20260324.md) に移動済み。

