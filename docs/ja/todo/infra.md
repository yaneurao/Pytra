<a href="../../en/todo/infra.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — インフラ・ツール・仕様

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-30

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。

完了済みタスクは [アーカイブ](archive/20260428.md) を参照。

## 未完了タスク

### P2-TOP100-LANGUAGE-COVERAGE: 使用上位 100 言語への適応範囲を管理する

文脈: [docs/ja/plans/p2-top100-language-coverage.md](../plans/p2-top100-language-coverage.md)

TIOBE Index 2026-04 の top 100 を初期スナップショットとして、Pytra がどの言語へどの深さで適応できるかを coverage matrix で管理する。全 100 言語を一律 native backend 化するのではなく、`backend` / `host` / `interop` / `syntax` / `defer` に分類して進める。

1. [x] [ID: P2-TOP100-LANG-S1] top 100 言語 catalog を machine-readable にする（rank/source/category/current_status）
   - 入力正本: `docs/ja/plans/p2-top100-language-coverage.md`
   - 出力候補: `specs/top100-language-coverage.yaml` または `docs/ja/progress/top100-language-coverage.md`
   - 完了: 2026-04-30。公式 TIOBE April 2026 を再確認し、`docs/ja/progress/top100-language-coverage.md` に source snapshot、100言語 matrix、分類、実測コマンド、blocker、次アクションを固定した。
2. [x] [ID: P2-TOP100-LANG-S2] 既存 backend / host / interop / syntax / defer の初期分類を確定する
   - 既存 backend 群: cpp, rs, cs, js, ts, dart, go, java, scala, kotlin, swift, ruby, lua, php, nim, julia, zig, powershell を現状 matrix に接続する。
   - 完了: 2026-04-30。Top100 matrix で Pytra 既存 target を `backend` / Python を `host` / C と SQL 系を `interop` / 未接続候補を `syntax` / visual・platform-specific・historical 系を `defer` に初期分類した。
3. [x] [ID: P2-TOP100-LANG-S3] top 50 の未対応候補から優先 backend plan を作る
   - 初期候補: Visual Basic, R, Delphi/Object Pascal, Perl, Fortran, MATLAB, Ada, PL/SQL, Prolog, COBOL, SAS, Objective-C, Lisp, ML, Haskell, VBScript, ABAP, OCaml, Caml, Erlang, X++, Transact-SQL, Solidity。
   - 完了: 2026-04-30。`tools/gen/gen_top100_language_coverage.py` で Top50 syntax 候補に T1/T2/T3 の backend plan を生成し、`docs/ja/progress/top100-language-coverage.md` へ反映した。
4. [x] [ID: P2-TOP100-LANG-S4] DSL / visual / shell / query 系の defer 条件を明文化する
   - 対象例: SQL, Scratch, Assembly language, GML, LabVIEW, Ladder Logic, FoxPro, Pure Data, VHDL, Wolfram など。
   - 完了: 2026-04-30。defer row に解除条件を持たせ、visual/block/dataflow/platform-specific/proprietary/historical/niche runtime の保留理由を `docs/ja/progress/top100-language-coverage.md` と JSON に出力するようにした。
5. [x] [ID: P2-TOP100-LANG-S5] `gen_backend_progress.py` または新規 progress generator で top100 coverage を自動出力する
   - 出力には source snapshot date、分類、実測コマンド、最後の blocker、次アクションを含める。
   - 完了: 2026-04-30。`tools/gen/gen_top100_language_coverage.py` で JA/EN Markdown と `docs/ja/progress/top100-language-coverage.json` を生成し、`--check` を stale 検出ゲートにした。
6. [x] [ID: P2-TOP100-LANG-S6] devcontainer / Docker 検証を top100 coverage 更新の標準ゲートにする
   - Docker Desktop 同梱 CLI が PATH に無い場合は `/Applications/Docker.app/Contents/Resources/bin/docker` を使う。
   - Docker が使えない run では coverage を完了扱いにせず、exact blocker と再開条件だけを残す。
   - 完了: 2026-04-30。`docker version` / `docker run --rm hello-world` / `.devcontainer/Dockerfile` build / `.devcontainer/scripts/verify-toolchain.sh` を標準 gate とし、常設 `devcontainer` CLI 不在時は Dockerfile 直接 run に fallback する手順を progress に固定した。

### P1-EMITTER-HOST-MATRIX: emitter host マトリクスの新設と全言語 PASS

文脈: [docs/ja/plans/p1-emitter-host-matrix.md](../plans/p1-emitter-host-matrix.md)

selfhost マトリクス（full compiler）とは別に、「C++ emitter（16 モジュール）を各言語で host できるか」の emitter host マトリクスを新設する。全 18 言語で PASS を中間目標とする。

1. [x] [ID: P1-EHOST-MATRIX-S1] `gen_backend_progress.py` に emitter host マトリクス生成を追加する（`.parity-results/emitter_host_<lang>.json` から読み取り）
   - 完了: 2026-04-29。`_load_emitter_host_results()` と build/parity のアイコン化を追加した。
2. [x] [ID: P1-EHOST-MATRIX-S2] `progress-preview/backend-progress-emitter-host.md` を出力するようにする
   - 完了: 2026-04-29。`python3 tools/gen/gen_backend_progress.py` で JA/EN の `backend-progress-emitter-host.md` を生成するようにした。
3. [x] [ID: P1-EHOST-MATRIX-S3] 各 backend の P1-HOST-CPP-EMITTER タスクの S2 で `.parity-results/emitter_host_<lang>.json` に結果を書き込むよう更新する
   - 完了: 2026-04-29。各 backend TODO の S2 を emitter host 結果 JSON へ向けた。
4. [x] [ID: P1-EHOST-MATRIX-S4] JSON 形式を N×N 対応に拡張する（1ファイルに複数 hosted emitter の結果を持てるようにする）
   - 完了: 2026-04-29。`emitter_host_<host_lang>.json` の `emitters` map を正本形式として読み込むようにした。
5. [x] [ID: P1-EHOST-MATRIX-S5] `gen_backend_progress.py` を N×N マトリクス表示に対応させる（行: host 言語、列: hosted emitter）
   - 完了: 2026-04-29。`backend-progress-emitter-host.md` を host 言語 × hosted emitter の N×N 表示へ変更した。

### P2-TOP100-LANGUAGE-COVERAGE: 使用上位 100 言語への適応を分類管理する

文脈: [docs/ja/plans/p2-top100-language-coverage.md](../plans/p2-top100-language-coverage.md)

使用上位 100 言語への適応は、一律 backend 化ではなく `backend` / `host` / `interop` / `syntax` / `defer` の分類で進める。

1. [x] [ID: P2-TOP100-LANGUAGE-COVERAGE-S1] 外部 Top100 source snapshot を固定し、取得日・URL・保存場所を記録する
   - 進捗: 2026-04-29。本 run では外部 source 未固定。repo-local snapshot として `docs/ja/progress/backend-progress-summary.md` の 18 言語と `src/pytra-cli.py -build` の target 一覧を `docs/ja/plans/p2-top100-language-coverage.md` に固定した。
   - 完了: 2026-04-30。`docs/ja/progress/top100-language-coverage.md` に TIOBE Index for April 2026 の URL、取得日、保存場所を記録した。
2. [x] [ID: P2-TOP100-LANGUAGE-COVERAGE-S2] 100 言語を `backend` / `host` / `interop` / `syntax` / `defer` に分類する
   - 進捗: 2026-04-29。分類軸を plan に追加した。外部 source 未固定のため、100 言語表は未作成。
   - 完了: 2026-04-30。100 言語表を作成し、各行に分類、current status、last blocker、next action を付与した。
3. [x] [ID: P2-TOP100-LANGUAGE-COVERAGE-S3] `backend` / `host` 候補を既存 progress matrix に接続し、`interop` / `syntax` / `defer` は個別 plan へ分離する
   - 完了: 2026-04-30。Top100 generator で既存 backend / host を progress matrix の blocker と next action に接続し、Top50 syntax plan と defer 条件を個別 section と JSON fields に分離した。

### 保留中タスク

- P20-INT32 は [plans/p4-int32-default.md](../plans/p4-int32-default.md) に保留中。再開時にここへ戻す。
