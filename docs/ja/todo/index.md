# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-04

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

### P0: 画像runtime 構成是正（`pytra-core` / `pytra-gen` 分離 + 正本自動生成）

文脈: [docs/ja/plans/p0-image-runtime-core-gen-rollout.md](../plans/p0-image-runtime-core-gen-rollout.md)

1. [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01] 全言語の画像runtimeを `pytra-core`（手書き）と `pytra-gen`（`src/pytra/utils/{png,gif}.py` 由来生成物）へ物理分離し、旧「marker中心」運用を廃止する。
2. [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S1-01] 旧 `P0-IMAGE-RUNTIME-SOT-LANG-01` を誤った実現方式として廃止し、TODOから削除した履歴を計画書へ明記する。
3. [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S1-02] 画像runtimeの責務境界（`pytra-core` 禁止事項 / `pytra-gen` 必須事項 / 正本変更禁止）を `docs/ja/spec` と `docs/en/spec` に追記する。
4. [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S2-01] 各バックエンド共通の生成導線（`png.py/gif.py -> <lang> runtime`）と出力先規約（`src/runtime/<lang>/{pytra-core,pytra-gen}`）を実装する。
5. [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S2-02] `tools/audit_image_runtime_sot.py` を「marker有無」から「`pytra-gen` 実体 + 生成痕跡 + core混入禁止」検査へ置換する。
6. [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-RS] Rust runtime を `pytra-core` / `pytra-gen` 分離へ移行し、画像関数を `py_runtime.rs` から撤去する。
7. [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-GO] Go runtime を `pytra-core` / `pytra-gen` 分離へ移行し、画像関数を `py_runtime.go` から撤去する。
8. [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-JAVA] Java runtime を `pytra-core` / `pytra-gen` 分離へ移行し、画像関数を `PyRuntime.java` から撤去する。
9. [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-SWIFT] Swift runtime を `pytra-core` / `pytra-gen` 分離へ移行し、画像関数を `py_runtime.swift` から撤去する。
10. [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-KOTLIN] Kotlin runtime を `pytra-core` / `pytra-gen` 分離へ移行し、画像関数を `py_runtime.kt` から撤去する。
11. [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-RUBY] Ruby runtime を `pytra-core` / `pytra-gen` 分離へ移行し、画像関数を `py_runtime.rb` から撤去する。
12. [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-LUA] Lua runtime を `pytra-core` / `pytra-gen` 分離へ移行し、画像関数を `py_runtime.lua` から撤去する。
13. [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-PHP] PHP runtime を `pytra-core` / `pytra-gen` 分離へ移行し、画像関数を `py_runtime.php` / `runtime/*.php` の責務境界に沿って再配置する。
14. [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-CS] C# runtime を `pytra-core` / `pytra-gen` 分離へ移行し、画像関数を `py_runtime.cs` 直埋めから撤去する。
15. [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-JS] JavaScript runtime を `pytra-core` / `pytra-gen` 分離へ移行し、画像helperを生成物ディレクトリへ集約する。
16. [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-TS] TypeScript runtime を `pytra-core` / `pytra-gen` 分離へ移行し、画像helperを生成物ディレクトリへ集約する。
17. [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-SCALA] Scala3 runtime を `pytra-core` / `pytra-gen` 分離へ移行し、画像関数を `py_runtime.scala` 直埋めから撤去する。
18. [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-NIM] Nim runtime を `pytra-core` / `pytra-gen` 分離へ移行し、画像関数を `py_runtime.nim` 直埋めから撤去する。
19. [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S4-01] 全言語で `sample/01,05` parity（stdout + artifact size + CRC32）を再確認する。
20. [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S4-02] 各backendの runtime copy hook / build手順を新レイアウトへ更新する。
21. [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S4-03] CI/ローカル検査へ「`pytra-core` に画像実装が混入したらfail」を追加する。
- 進捗メモ: [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S1-02] `docs/ja/spec/spec-{codex,dev}.md` と `docs/en/spec/spec-{codex,dev}.md` に `pytra-core` / `pytra-gen` の責務境界（core直書き禁止・gen生成痕跡必須）を追記して完了。
- 進捗メモ: [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S2-01] `tools/gen_image_runtime_from_canonical.py` を追加し、`png.py/gif.py -> src/runtime/<lang>/pytra-gen/...` の共通生成計画（14言語）を実装。`--dry-run` と `test_gen_image_runtime_from_canonical.py` で導線を検証。
- 進捗メモ: [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S2-02] `tools/audit_image_runtime_sot.py` を core/gen 検査へ置換（`pytra-core` 混入禁止、`pytra-gen` の `source:` / `generated-by:` 必須、legacy配置検知）。`image_runtime_core_gen_audit_20260304_s2_02.json` を取得し baseline（`compliant=1/non_compliant=13`）を固定。
- 進捗メモ: [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-RS] `src/runtime/rs/pytra-core/built_in/py_runtime.rs` と `src/runtime/rs/pytra-gen/utils/image_runtime.rs` を追加し、Rust runtime hook を core+gen コピーへ変更。`runtime_parity_sample_rs_0105_core_gen_split_retry_20260304.json` で `sample/01,05` parity pass を確認。
- 進捗メモ: [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-GO] `src/runtime/go/pytra-core/built_in/py_runtime.go` と `src/runtime/go/pytra-gen/utils/{png.go,gif.go}` を追加し、Go runtime hook を core+gen コピーへ変更。`runtime_parity_sample_go_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 進捗メモ: [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-JAVA] `src/runtime/java/pytra-core/built_in/PyRuntime.java` と `src/runtime/java/pytra-gen/utils/{PngHelper.java,GifHelper.java}` を追加し、Java runtime hook を core+gen コピーへ変更。`runtime_parity_sample_java_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。

### P0: 画像runtime 静的ガードレール導入（core混入禁止）

文脈: [docs/ja/plans/p0-image-runtime-static-guardrails.md](../plans/p0-image-runtime-static-guardrails.md)

1. [ ] [ID: P0-IMAGE-RUNTIME-STATIC-GUARDRAILS-01] `pytra-core` への画像実装混入を静的検査で検知し、CI必須チェックとして固定する。
2. [ ] [ID: P0-IMAGE-RUNTIME-STATIC-GUARDRAILS-01-S1-01] 検査仕様（許可パス/禁止シンボル/必須marker/除外規則）を定義する。
3. [ ] [ID: P0-IMAGE-RUNTIME-STATIC-GUARDRAILS-01-S2-01] `tools/` に静的検査スクリプトを実装し、`pytra-core` 混入を fail できるようにする。
4. [ ] [ID: P0-IMAGE-RUNTIME-STATIC-GUARDRAILS-01-S2-02] `pytra-gen` 生成痕跡（`source:`/`generated-by:`）欠落を fail する検査を追加する。
5. [ ] [ID: P0-IMAGE-RUNTIME-STATIC-GUARDRAILS-01-S3-01] 検査スクリプトの unit test を追加する（正常系/違反系）。
6. [ ] [ID: P0-IMAGE-RUNTIME-STATIC-GUARDRAILS-01-S3-02] `tools/run_local_ci.py` と CI 導線に必須ジョブとして組み込む。
7. [ ] [ID: P0-IMAGE-RUNTIME-STATIC-GUARDRAILS-01-S4-01] 既存runtimeへ検査を適用し、全言語で green を確認する。

### P0: PHP sample parity 全件完了（stdout + artifact CRC32）

文脈: [docs/ja/plans/p0-php-sample-parity-complete.md](../plans/p0-php-sample-parity-complete.md)

1. [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01] PHP の `sample` parity（stdout + artifact size + CRC32）を全18件で完了させる。
2. [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S1-01] PHP `sample` 全件 parity を再実行し、単独 target の最新 baseline を固定する。
3. [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S1-02] fail 8件（`05,06,08,10,11,12,14,16`）の artifact 差分をケース別に切り分ける。
4. [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-01] PHP GIF runtime を Python 実装準拠へ揃え、GIF 系 CRC mismatch を解消する。
5. [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-02] PHP PNG runtime を再検証し、必要な差分を修正する。
6. [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-03] PHP lower/emitter の画像出力入力（palette/frame/list/bytes 経路）を是正する。
7. [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-04] `sample/13` の stdout mismatch 再発有無を検証し、未解消なら根本修正する。
8. [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-01] `--targets php --all-samples` を再実行し、`case_pass=18` / `case_fail=0` を確認する。
9. [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-02] 修正内容に対応する回帰テストを追加して再発防止を固定する。
10. [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-03] 生成ログと決定事項を計画書へ記録し、TODO の完了条件を明示する。
- 進捗メモ: [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-03] `save_gif` keyword 引数欠落と bit 演算崩れを PHP emitter で修正し、`work/logs/runtime_parity_sample_php_all_pass_20260304.json` で `case_pass=18/case_fail=0`（`ok:18`）を確認。

### P1: `test/unit` レイアウト再編と未使用テスト整理

文脈: [docs/ja/plans/p1-test-unit-layout-and-pruning.md](../plans/p1-test-unit-layout-and-pruning.md)

1. [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01] `test/unit` を責務別フォルダへ再編し、未使用テストを根拠付きで整理する。
2. [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-01] `test/unit` の現行テストを責務分類（common/backends/ir/tooling/selfhost）で棚卸しし、移動マップを確定する。
3. [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-02] 目標ディレクトリ規約を定義し、命名・配置ルールを決定する。
4. [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-01] テストファイルを新ディレクトリへ移動し、`tools/` / `docs/` の参照パスを一括更新する。
5. [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-02] `unittest discover` と個別実行導線が新構成で通るように CI/ローカルスクリプトを更新する。
6. [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-01] 未使用テスト候補を抽出し、`削除/統合/維持` を判定する監査メモを作成する。
7. [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-02] 判定済みの未使用テストを削除または統合し、再発防止チェック（必要なら新規）を追加する。
8. [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-01] 主要 unit/transpile/selfhost 回帰を実行し、再編・整理後の非退行を確認する。
9. [x] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-02] `docs/ja/spec`（必要なら `docs/en/spec`）へ新しいテスト配置規約と運用手順を反映する。
- 進捗メモ: [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-01] `test/unit` 71本を棚卸しし、移動マップを `backends/*:29, ir:10, tooling:5, selfhost:3, common:23` で確定。`S2-01` でこの分類に従って再編する。
- 進捗メモ: [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-02] `test/unit/{common,backends/<lang>,ir,tooling,selfhost}` の目標配置・命名・discover運用規約を計画書に確定し、`test/unit` 直下直置き禁止を明文化。
- 進捗メモ: [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-01] `test/unit/test_*.py` 71本を責務別ディレクトリへ移動し、`run_local_ci.py` と `check_noncpp_east3_contract.py` の固定参照を新パスへ更新。`backends` 名衝突回避のため `test/unit/backends` は非package運用とした。
- 進捗メモ: [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-02] `test_discovery_router` を手動ローダ化して非package再帰 discover を復旧し、`comment_fidelity` import 失敗を root helper 追加で解消。`go/swift/kotlin` の個別 discover も新パスで通過。
- 進捗メモ: [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-01] 参照スキャンで抽出した未使用候補（`test_pylib_*`, `test_east3_to_human_repr.py`）を個別 discover で再検証し、現役回帰として `維持` 判定。削除・統合候補は 0 件。
- 進捗メモ: [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-02] `S3-01` 監査結果により削除・統合対象は 0 件のため no-op クローズ。再発防止は配置規約と discover ルータで継続運用。
- 進捗メモ: [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-01] `test_py2x_smoke_common`, `py2{go,swift,kotlin}_smoke`, `selfhost/test_prepare_selfhost_source`, `check_noncpp_east3_contract --skip-transpile` を再実行し全通過を確認。
- 進捗メモ: [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-02] `docs/ja/spec` / `docs/en/spec` のテスト参照パスを新配置（`common/backends/ir/tooling/selfhost`）へ更新し運用手順を同期。

### P1: Nim sample parity 完了化（runtime_parity_check 正式統合）

文脈: [docs/ja/plans/p1-nim-sample-parity-complete.md](../plans/p1-nim-sample-parity-complete.md)

1. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01] Nim を parity 回帰対象へ正式統合し、`sample` 18件の stdout + artifact（size + CRC32）一致を完了させる。
2. [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-01] `runtime_parity_check` に Nim target（transpile/run/toolchain 判定）を追加する。
3. [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-02] `regenerate_samples.py` に Nim を追加し、`sample/nim` 再生成導線を固定する。
4. [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-03] Nim `sample` 全件 parity を実行して失敗カテゴリを固定する。
5. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-01] Nim runtime の PNG writer 手実装を撤去し、`src/pytra/utils/png.py` 正本由来の生成物へ置換する。
6. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-02] Nim runtime の GIF writer 手実装を撤去し、`src/pytra/utils/gif.py` 正本由来の生成物へ置換する。
7. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-03] Nim emitter/lower の画像出力経路と runtime 契約を整合させる。
8. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-04] 残件ケース（例: `sample/18`）を最小修正で解消する。
9. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-01] `--targets nim --all-samples` で `case_pass=18` / `case_fail=0` を確認する。
10. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-02] Nim parity 契約の回帰テスト（CLI/smoke/transpile）を更新する。
11. [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-03] 検証ログと運用手順を計画書へ記録し、クローズ条件を明文化する。
- 進捗メモ: [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-01] `runtime_parity_check` に Nim target を追加し、モジュール名制約回避のため `case_<stem>.nim` 出力で実行可能化。`test_runtime_parity_check_cli.py` に Nim エントリ回帰を追加。
- 進捗メモ: [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-02] `regenerate_samples.py --langs nim --force` を通し、`summary: total=18 skip=0 regen=18 fail=0` で Nim 再生成導線を固定。
- 進捗メモ: [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-03] Nim sample parity baseline を実行し、`work/logs/runtime_parity_sample_nim_rebaseline_20260304.json` で `case_pass=0/case_fail=18`、`run_failed=16/output_mismatch=2` を固定。
- 進捗メモ: [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-01] Nim runtime の `write_rgb_png` を pure Nim 実装へ置換し、`work/logs/runtime_nim_png_crc_check_20260304.json` で `sample/01` の PNG artifact `size+crc32` 一致を確認。
- 進捗メモ: [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-02] Nim runtime に `grayscale_palette/save_gif` を実装し、`work/logs/runtime_nim_gif_crc_check_20260304.json` で GIF artifact の `size+crc32` 一致を確認。
- 進捗メモ: [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-01] 運用是正により手実装完了を無効化。`png/gif` は Python正本由来のみ許可とし、`S2-01/S2-02` を「手実装撤去＋生成物置換」の未完了タスクとして再オープン。

### P2: 多言語 runtime の C++ 同等化（API 契約・機能カバレッジ統一）

文脈: [docs/ja/plans/p2-runtime-parity-with-cpp.md](../plans/p2-runtime-parity-with-cpp.md)

1. [ ] [ID: P2-RUNTIME-PARITY-CPP-01] C++ runtime を基準に、他言語 runtime の API 契約と機能カバレッジを段階的に同等化する。
2. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-01] C++ runtime の必須 API カタログ（module/function/契約）を抽出する。
3. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-02] 各言語 runtime の実装有無マトリクスを作成し、欠落/互換/挙動差を分類する。
4. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-03] 同等化対象を `Must/Should/Optional` で優先度付けする。
5. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1（`go/java/kotlin/swift`）で `math/time/pathlib/json` 不足 API を実装する。
6. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S2-01-S1-01] Wave1-Go: `json.loads/dumps` runtime API を追加し、Go emitter の `json.*` 呼び出しを runtime helper へ統一する。
7. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-02] Wave1 の emitter 呼び出しを adapter 経由へ寄せ、API 名揺れを吸収する。
8. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-03] Wave1 の parity 回帰を追加し、runtime 差由来 fail を固定する。
9. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-01] Wave2（`ruby/lua/scala/php`）で不足 API を実装する。
10. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-02] Wave2 の emitter 呼び出しを adapter 経由へ寄せる。
11. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-03] Wave2 の parity 回帰を追加し、runtime 差由来 fail を固定する。
12. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-01] Wave3（`js/ts/cs/rs`）で不足 API を補完し、契約差を解消する。
13. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-02] runtime API 欠落検知チェックを追加し、CI/ローカル回帰へ組み込む。
14. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-03] `docs/ja/spec` / `docs/en/spec` に runtime 同等化ポリシーと進捗表を反映する。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S1-01] `docs/ja/spec/spec-runtime.md` に C++ runtime API 正本カタログ（Must/Should）を追加し、Wave 同等化の基準 API を固定。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S1-02] `src/runtime/<lang>/pytra` 棚卸し結果を `native/mono/compat/missing` でマトリクス化し、主要欠落（json/pathlib/gif）を分類。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S1-03] マトリクス差分を `Must/Should/Optional` へ優先度化し、Wave1/2/3 の着手順（json/pathlib/gif優先）を確定。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01-S1-01] Go runtime に `pyJsonLoads/pyJsonDumps` を追加し、Go emitter の `json.loads/json.dumps` を runtime helper へ統一。`test_py2go_smoke.py` と `check_py2go_transpile.py` で非退行確認。

### P4: 全言語 selfhost 完全化（低低優先）

文脈: [docs/ja/plans/p4-multilang-selfhost-full-rollout.md](../plans/p4-multilang-selfhost-full-rollout.md)

1. [ ] [ID: P4-MULTILANG-SH-01] `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala` の selfhost を段階的に成立させ、全言語の multistage 監視を通過可能にする。
2. [ ] [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost の stage2 依存 transpile 失敗を解消し、multistage を通す。
3. [ ] [ID: P4-MULTILANG-SH-01-S3-01] TypeScript の preview-only 状態を解消し、selfhost 実行可能な生成モードへ移行する。
4. [ ] [ID: P4-MULTILANG-SH-01-S3-02] Go/Java/Swift/Kotlin の native backend 化タスクと接続し、selfhost 実行チェーンを有効化する。
5. [ ] [ID: P4-MULTILANG-SH-01-S3-03] Ruby/Lua/Scala3 を selfhost multistage 監視対象へ追加し、runner 未定義状態を解消する。
6. [ ] [ID: P4-MULTILANG-SH-01-S4-01] 全言語 multistage 回帰を CI 導線へ統合し、失敗カテゴリの再発を常時検知できるようにする。
7. [ ] [ID: P4-MULTILANG-SH-01-S4-02] 完了判定テンプレート（各言語の stage 通過条件と除外条件）を文書化し、運用ルールを固定する。
- 完了済み子タスク（`S1-01` 〜 `S2-02-S3`）および過去進捗メモは `docs/ja/todo/archive/20260301.md` へ移管済み。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] JS emitter の selfhost parser 制約違反（`Any` 受け `node.get()/node.items()`）と関数内 `FunctionDef` 未対応を解消し、先頭失敗を `stage1_dependency_transpile_fail` から `self_retranspile_fail (ERR_MODULE_NOT_FOUND: ./pytra/std.js)` まで前進。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost 準備に shim 生成・import 正規化・export 注入・構文置換を追加し、`ERR_MODULE_NOT_FOUND` を解消。先頭失敗は `SyntaxError: Unexpected token ':'`（`raw[qpos:]` 由来）へ遷移。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost 向けに slice/集合判定の source 側縮退、ESM shim 化、import 正規化再設計、`argparse`/`Path` 互換 shim、`.py -> EAST3(JSON)` 入力経路、`JsEmitter` profile loader の selfhost 互換化を段階適用。先頭失敗は `ReferenceError/SyntaxError` 群を解消して `TypeError: CodeEmitter._dict_copy_str_object is not a function` へ遷移。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] `CodeEmitter.load_type_map` と `js_emitter` 初期化の dict access を object-safe 化し、selfhost rewrite に `set/list/dict` polyfill と `CodeEmitter` static alias 補完を追加。先頭失敗は `dict is not defined` を解消して `TypeError: module.get is not a function` へ前進。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] selfhost rewrite を `.get -> __pytra_dict_get` 化し、`Path` shim に `parent/name/stem` property 互換と `mkdir(parents/exist_ok)` 既定冪等化を追加。`js` は `stage1 pass / stage2 pass` に到達し、先頭失敗は `stage3 sample output missing` へ遷移。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] `CodeEmitter/JsEmitter` の object-safe 変換（`startswith/strip/find` 依存除去、`next_tmp` f-string 修正、ASCII helperの `ord/chr` 依存撤去）と selfhost rewrite の String polyfill（`strip/lstrip/rstrip/startswith/endswith/find/lower/upper/map`）を追加。`js` は `stage1/native pass`・`multistage stage2 pass` を維持し、先頭失敗は `stage3 sample_transpile_fail (SyntaxError: Invalid or unexpected token)` へ前進。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] `emit` のインデント生成（文字列乗算）を loop 化し、`quote_string_literal` の `quote` 非文字列防御、`_emit_function` の `in_class` 判定を `None` 依存から空文字判定へ変更。`js` は `stage1/native pass`・`multistage stage2 pass` を維持し、先頭失敗は `stage3 sample_transpile_fail (SyntaxError: Unexpected token '{')` に更新（`py2js_stage2.js` の未解決 placeholder/関数ヘッダ崩れが残件）。
