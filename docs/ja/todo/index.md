# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-07

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

### P0: linked program 導入（multi-unit optimizer + ProgramWriter 分離）

文脈: [docs/ja/plans/p0-linked-program-global-optimizer-and-program-writer.md](../plans/p0-linked-program-global-optimizer-and-program-writer.md)

1. [ ] [ID: P0-LINKED-PROGRAM-OPT-01] linked program を導入し、global optimizer の入力単位を複数翻訳単位へ拡張しつつ、backend を `ModuleEmitter + ProgramWriter` 構成へ再編する。
2. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S1-01] `link-input.v1` / `link-output.v1` と linked module `meta` の schema、ならびに `spec-linker` / `spec-east` の責務境界を固定する。
3. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S1-02] `ModuleArtifact` / `ProgramArtifact` / `ProgramWriter` の backend 共通契約を定義し、`spec-dev` / `spec-make` へ反映する。
4. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S2-01] `src/toolchain/link/` に `LinkedProgram` loader / validator / manifest I/O を追加し、複数 `EAST3` を deterministic に読めるようにする。
5. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S2-02] `py2x.py` の in-memory 導線を module map から `LinkedProgram` 構築へ切り替え、single-module 前提を外す。
6. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S3-01] program-wide call graph / SCC fixed point を linker 段へ実装し、import-closure 内部読込に依存しない global 解析基盤を作る。
7. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S3-02] global non-escape / container ownership / `type_id` 決定を linker 段へ実装し、linked module と `link-output.json` へ materialize する。
8. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S4-01] `EAST3 local optimizer` と `LinkedProgramOptimizer` の pass 責務を再分割し、whole-program 依存 pass を local optimizer から撤去する。
9. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S5-01] `backend_registry.py` を `emit_module + program_writer` 契約へ拡張し、旧 `emit -> str` API を互換 wrapper 化する。
10. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S5-02] backend 共通 `SingleFileProgramWriter` を追加し、`ir2lang.py` を new registry 契約へ追従させる。
11. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S6-01] C++ を先行移行し、`multifile_writer.py` を `CppProgramWriter` へ再編して `CppEmitter` を module emit 専任にする。
12. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S6-02] `pytra-cli.py` / C++ build manifest / Makefile 生成導線を `ProgramWriter` 返却 manifest 正本へ更新する。
13. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S7-01] `eastlink.py` を追加し、`link-input.json -> link-output.json + linked modules` の debug/restart 導線を実装する。
14. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S7-02] `ir2lang.py` と `py2x.py` に linked-program 入出力（`--link-only`, dump/restart）を追加し、backend-only 導線を完成させる。
15. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S8-01] `test/unit/link/*` と representative backend/tooling 回帰を追加し、schema / determinism / program writer 契約を固定する。
16. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S8-02] C++ unit / fixture / sample parity、docs 同期、旧 import-closure 依存経路の撤去まで完了し、本計画を閉じる。
