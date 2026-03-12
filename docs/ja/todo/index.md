# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-12

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

1. [ ] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01] `dataclasses.field(...)` を runtime call ではなく静的 dataclass metadata subset として扱い、representative lane を fail-closed contract 付きで固定する。
   文脈: [p1-dataclass-field-static-subset.md](/workspace/Pytra/docs/ja/plans/p1-dataclass-field-static-subset.md)
   概要: Pytra-NES の `timestamps: deque[float] = field(init=False, repr=False)` のような representative case で、現状は `field(...)` が通常の式として backend へ漏れて壊れたコードを生成する。v1 では `default` / `default_factory` / `init` / `repr` / `compare` を静的 metadata subset として扱い、unsupported option は fail-closed にする。進捗: `S3-01` で `repr` / `compare` metadata と unsupported option / duplicate option / `default` + `default_factory` conflict の fail-closed regression を固定した。

2. [ ] [ID: P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01] `py_runtime.h` に残っている object-bridge mutation seam と shared `type_id` thin seam を cross-runtime 契約の整理後に最小化する。
   文脈: [p5-cpp-pyruntime-residual-thin-seam-shrink.md](/workspace/Pytra/docs/ja/plans/p5-cpp-pyruntime-residual-thin-seam-shrink.md)
   概要: 現在の `py_runtime.h` は以前よりかなり縮小済みだが、`py_append(object&)` と `py_runtime_value_*` / `py_runtime_object_*` / `py_runtime_type_id_*` の thin seam が残っている。これらは header 単体では削れず、C++ / Rust / C# emitter と runtime の shared contract 整理を伴うので、後段の `P5` として bundle 単位で縮退計画を固定する。

3. [ ] [ID: P5-POWERSHELL-CS-HOST-01] PowerShell backend を新設する代わりに、C# backend の出力を `pwsh` から build / run する host profile を整理する。
   文脈: [p5-powershell-csharp-host-profile.md](/workspace/Pytra/docs/ja/plans/p5-powershell-csharp-host-profile.md)
   概要: `py2cs` の generated `.cs` と runtime 同梱物を `pwsh` から representative に起動する host profile を定義し、Windows / PowerShell 7 / `.NET` 系 toolchain を前提に `dotnet` / `csc` / `Add-Type` の優先順と fail-closed 条件を固定する。pure PowerShell backend は対象外とする。

4. [ ] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01] cross-backend backend parity matrix を実際の `feature × backend` support-state table として埋め、全 backend の canonical source にする。
   文脈: [p6-backend-parity-matrix-cell-fill.md](/workspace/Pytra/docs/ja/plans/p6-backend-parity-matrix-cell-fill.md)
   概要: 現在の parity matrix は row seed と state taxonomy を持つ scaffold だが、各 cell の support state はまだ埋まっていない。C++ 個別 matrix を drill-down にとどめ、全 backend を横断した canonical 2 次元表を `support_state` / `evidence_kind` 付きで実体化する。
