# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-09

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

1. [ ] [ID: P1-LINKED-HELPER-ARTIFACT-01] linked-program optimizer から helper artifact を正規出力できるようにする。
- [x] [ID: P1-LINKED-HELPER-ARTIFACT-01-S1-01] 現状の helper 逃し先と blocker を棚卸しする。
- 進捗メモ: [ID: P1-LINKED-HELPER-ARTIFACT-01-S1-01] helper の escape hatch は `py_runtime.h`、checked-in/generated runtime、C++ emitter の special-op include、backend-local inline helper に分散しており、blocker は `LinkedProgramModule` / `link-output.json` / materializer / validator / writer が helper kind を持てない点だと固定した。
- [x] [ID: P1-LINKED-HELPER-ARTIFACT-01-S1-02] helper artifact schema / module kind / metadata 契約を spec に固定する。
- 進捗メモ: [ID: P1-LINKED-HELPER-ARTIFACT-01-S1-02] `spec-linker` / `spec-dev` / `spec-east` に `module_kind=helper`、`meta.synthetic_helper_v1`、`helper_id/owner_module_id/generated_by`、single-file fold でも runtime 再探索へ戻さない契約を追加した。
- [x] [ID: P1-LINKED-HELPER-ARTIFACT-01-S2-01] linked-program model / validator / materializer を helper-aware にする。
- 進捗メモ: [ID: P1-LINKED-HELPER-ARTIFACT-01-S2-01] `LinkedProgramModule` / `LinkOutputModuleEntry` に `module_kind/helper_id/owner_module_id/generated_by` を追加し、validator・materializer・global pass・template specialization が helper metadata を保持したまま `link-output` / reload できることを link test で固定した。
- [x] [ID: P1-LINKED-HELPER-ARTIFACT-01-S2-02] `link-output.json` / restart 導線へ helper module lane を追加する。
- 進捗メモ: [ID: P1-LINKED-HELPER-ARTIFACT-01-S2-02] `ir2lang` の `link-output` restart regression を追加し、`module_kind=helper` かつ `source_path=""` の helper entry が synthetic fallback path を使って C++ multi-file writer まで落ちずに渡ることを tooling test で固定した。
- [x] [ID: P1-LINKED-HELPER-ARTIFACT-01-S3-01] backend 共通 program artifact に `kind=helper` を追加する。
- 進捗メモ: [ID: P1-LINKED-HELPER-ARTIFACT-01-S3-01] host/static backend registry の `build_program_artifact()` と common/C++ program writer が module `kind` と helper metadata を保持し、single-file writer は helper module を primary 候補から除外することを contract test で固定した。
- [x] [ID: P1-LINKED-HELPER-ARTIFACT-01-S3-02] `CodeEmitter` / `ir2lang.py` / backend registry を helper-aware にする。
- 進捗メモ: [ID: P1-LINKED-HELPER-ARTIFACT-01-S3-02] `CodeEmitter` に helper artifact registry を追加し、host/static backend registry の `collect_program_modules()` と `py2x/ir2lang` が `emit_module()` の `helper_modules` を flatten して writer へ渡せることを CLI regression で固定した。
- [ ] [ID: P1-LINKED-HELPER-ARTIFACT-01-S4-01] C++ proof helper を synthetic helper module として materialize する。
- [ ] [ID: P1-LINKED-HELPER-ARTIFACT-01-S4-02] C++ `ProgramWriter` で helper を別ファイル化し、fixture/sample parity を確認する。
- [ ] [ID: P1-LINKED-HELPER-ARTIFACT-01-S5-01] representative single-file backend で helper fold 経路を確認する。
- [ ] [ID: P1-LINKED-HELPER-ARTIFACT-01-S5-02] docs / guard / archive を更新する。
