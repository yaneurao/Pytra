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
2. [x] [ID: P0-LINKED-PROGRAM-OPT-01-S1-01] `link-input.v1` / `link-output.v1` と linked module `meta` の schema、ならびに `spec-linker` / `spec-east` の責務境界を固定する。
3. [x] [ID: P0-LINKED-PROGRAM-OPT-01-S1-02] `ModuleArtifact` / `ProgramArtifact` / `ProgramWriter` の backend 共通契約を定義し、`spec-dev` / `spec-make` へ反映する。
4. [x] [ID: P0-LINKED-PROGRAM-OPT-01-S2-01] `src/toolchain/link/` に `LinkedProgram` loader / validator / manifest I/O を追加し、複数 `EAST3` を deterministic に読めるようにする。
5. [x] [ID: P0-LINKED-PROGRAM-OPT-01-S2-02] `py2x.py` の in-memory 導線を module map から `LinkedProgram` 構築へ切り替え、single-module 前提を外す。
6. [x] [ID: P0-LINKED-PROGRAM-OPT-01-S3-01] program-wide call graph / SCC fixed point を linker 段へ実装し、import-closure 内部読込に依存しない global 解析基盤を作る。
7. [x] [ID: P0-LINKED-PROGRAM-OPT-01-S3-02] global non-escape / container ownership / `type_id` 決定を linker 段へ実装し、linked module と `link-output.json` へ materialize する。
8. [x] [ID: P0-LINKED-PROGRAM-OPT-01-S4-01] `EAST3 local optimizer` と `LinkedProgramOptimizer` の pass 責務を再分割し、whole-program 依存 pass を local optimizer から撤去する。
9. [x] [ID: P0-LINKED-PROGRAM-OPT-01-S5-01] `backend_registry.py` を `emit_module + program_writer` 契約へ拡張し、旧 `emit -> str` API を互換 wrapper 化する。
10. [x] [ID: P0-LINKED-PROGRAM-OPT-01-S5-02] backend 共通 `SingleFileProgramWriter` を追加し、`ir2lang.py` を new registry 契約へ追従させる。
11. [x] [ID: P0-LINKED-PROGRAM-OPT-01-S6-01] C++ を先行移行し、`multifile_writer.py` を `CppProgramWriter` へ再編して `CppEmitter` を module emit 専任にする。
12. [x] [ID: P0-LINKED-PROGRAM-OPT-01-S6-02] `pytra-cli.py` / C++ build manifest / Makefile 生成導線を `ProgramWriter` 返却 manifest 正本へ更新する。
13. [x] [ID: P0-LINKED-PROGRAM-OPT-01-S7-01] `eastlink.py` を追加し、`link-input.json -> link-output.json + linked modules` の debug/restart 導線を実装する。
14. [x] [ID: P0-LINKED-PROGRAM-OPT-01-S7-02] `ir2lang.py` と `py2x.py` に linked-program 入出力（`--link-only`, dump/restart）を追加し、backend-only 導線を完成させる。
15. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S8-01] `test/unit/link/*` と representative backend/tooling 回帰を追加し、schema / determinism / program writer 契約を固定する。
16. [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S8-02] C++ unit / fixture / sample parity、docs 同期、旧 import-closure 依存経路の撤去まで完了し、本計画を閉じる。

### P0: backend から runtime module 知識を撤去する

文脈: [docs/ja/plans/p0-backend-runtime-knowledge-leak-retirement.md](../plans/p0-backend-runtime-knowledge-leak-retirement.md)

1. [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01] backend / emitter から source-side runtime module 名と ad-hoc helper ABI の知識を撤去し、resolved runtime symbol / semantic tag / adapter kind の data-driven 契約へ統一する。
2. [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S1-01] `src/backends/**` の `math/gif/png/save_gif/write_rgb_png/pyMath*` leakage を target 別・類型別に棚卸しし、代表ケースを固定する。
3. [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S1-02] `spec-runtime` / `spec-dev` に backend 禁止事項と resolved metadata 正規導線を明文化する。
4. [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S2-01] runtime symbol index / import binding API を拡張し、module import / function import / constant import / semantic tag を backend 外で解決できるようにする。
5. [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S2-02] helper ABI 差異を adapter kind へ正規化し、`save_gif` などの引数規約を emitter 直書きから外す。
6. [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-01] C++ / JS / CS / RS など代表 backend を resolved runtime symbol / adapter 描画へ移行する。
7. [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-02] Go / Swift / Kotlin / Java / Scala / Ruby / Lua / PHP / Nim を同じ契約へ追従させる。
8. [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S4-01] representative backend/test/tooling 回帰と guard を追加し、知識漏れの再侵入を防ぐ。
9. [ ] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S4-02] docs 同期と full smoke を実施し、本計画を閉じる。

### P1: generated/runtime helper 向け `@abi` decorator 導入

文脈: [docs/ja/plans/p1-runtime-abi-decorator-for-generated-helpers.md](../plans/p1-runtime-abi-decorator-for-generated-helpers.md)

1. [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01] generated/runtime helper の境界 ABI を固定できる `@abi` decorator を導入し、`@extern` と独立の boundary policy として扱えるようにする。
2. [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S1-01] `spec-abi` に `@abi` の syntax / semantics / mode / `@extern` との責務分離を明記する。
3. [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S1-02] `@abi` metadata の EAST / linked metadata 形式を決め、parser/selfhost parser の受け入れ基準を固定する。
4. [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S2-01] `src/pytra/std/__init__.py` に `abi` を追加し、parser / selfhost parser / AST build が decorator を保持できるようにする。
5. [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S2-02] `value_readonly` への mutation を検出する validator / lower guard を追加する。
6. [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S3-01] C++ backend に `@abi(args, ret)` の最小 lowering を実装し、helper signature を value ABI 正規形へ固定する。
7. [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S3-02] `py_join` など代表 helper を `@abi` 前提に移し、`rc<list<str>>` 非露出を回帰で固定する。
8. [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S4-01] `@extern` 併用 case / unsupported backend / invalid mutation case の unit test を追加する。
9. [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S4-02] docs 同期と `P1-CPP-PY-RUNTIME-SLIM-01` 依存解消メモを記録して本計画を閉じる。

### P1: C++ `py_runtime` を低レベル glue へ縮退させる

文脈: [docs/ja/plans/p1-cpp-py-runtime-core-slimming.md](../plans/p1-cpp-py-runtime-core-slimming.md)

1. [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01] `native/core/py_runtime.h` から pure Python で表現可能な built_in semantics を分離し、`core` を low-level ABI / object / container / process glue 中心へ縮退させる。
2. [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S1-01] `native/core/py_runtime.h` の function/class/helper を棚卸しし、`native/core` / `generated/core` / `generated/built_in` / `native/built_in` / 保留へ分類する。
3. [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S1-02] `spec-runtime` / `spec-dev` に `py_runtime` の責務境界と「残してよいもの / 戻すべきもの」を明文化する。
4. [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S2-01] `src/pytra/built_in/*.py` 側へ戻す候補を決め、SoT 上の配置案を固定する。
5. [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S2-02] `generated/core` または `generated/built_in` の emission lane に必要な generator / layout 契約を整備する。
6. [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S3-01] 文字列・collection 系の pure-Python built_in semantics を `native/core/py_runtime.h` から段階的に撤去し、正規の generated lane へ移す。
7. [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S3-02] `native/core/py_runtime.h` を low-level ABI / object / container / process glue 中心へ整理し、include 集約を最小化する。
8. [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S4-01] runtime symbol index / build graph / representative C++ runtime tests を新しい ownership に追従させる。
9. [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S4-02] fixture/sample parity・docs 同期・必要な guard 追加まで完了し、本計画を閉じる。

### P4: linked-program 後の非C++ backend 修復

文脈: [docs/ja/plans/p4-noncpp-backend-recovery-after-linked-program.md](../plans/p4-noncpp-backend-recovery-after-linked-program.md)

1. [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01] linked-program 導入後の non-C++ backend を `SingleFileProgramWriter` 前提の共通契約へ順次追従させ、broken state を family 単位で解消する。
2. [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S1-01] linked-program 後の non-C++ backend health matrix を作成し、各 target を failure category ごとに分類する。
3. [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S1-02] done 条件（static/smoke/transpile/parity/toolchain missing の扱い）と修復順序を spec/plan に固定する。
4. [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S2-01] `backend_registry.py` / `py2x.py` / `ir2lang.py` の non-C++ 互換層を点検し、`SingleFileProgramWriter` 前提の backend 共通契約不足を埋める。
5. [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S2-02] non-C++ backend health checker を追加または既存 checker を統合し、family 単位の broken/green を 1 コマンドで見られるようにする。
6. [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S3-01] Wave 1（`rs/cs/js/ts`）の static contract / smoke / transpile failure を解消し、compat route を安定化する。
7. [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S3-02] Wave 1 の parity baseline を更新し、runtime 差分と infra failure を分離する。
8. [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S4-01] Wave 2（`go/java/kotlin/swift/scala`）の static contract / smoke / transpile failure を解消する。
9. [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S4-02] Wave 2 の parity baseline を更新し、`toolchain missing` / 実行 failure / artifact 差分を固定化する。
10. [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S5-01] Wave 3（`ruby/lua/php/nim`）の static contract / smoke / transpile failure を解消する。
11. [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S5-02] Wave 3 の parity baseline を更新し、runtime 差分と backend bug を切り分ける。
12. [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S6-01] `run_local_ci.py` または同等の回帰導線へ non-C++ backend health check を統合する。
13. [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S6-02] `docs/ja/spec` / `docs/en/spec` / `docs/ja/how-to-use.md` を更新し、linked-program 後の non-C++ backend 修復運用を固定して計画を閉じる。
