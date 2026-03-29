<a href="../../en/todo/infra.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — インフラ・ツール・仕様

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-03-29

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。

## 未完了タスク

### P5-BACKEND-PROGRESS: parity 結果の自動蓄積 + 進捗ページ自動生成

文脈: [docs/ja/plans/p5-backend-progress.md](../plans/p5-backend-progress.md)

1. [ ] [ID: P5-PROGRESS-S1] `runtime_parity_check.py` / `runtime_parity_check_fast.py` が実行終了時に `work/parity-results/<target>_<case-root>.json` へ結果を無条件で書き出すようにする — 既存ファイルがあればケース単位でマージし、各ケースにタイムスタンプを付与する。`--summary-json` は追加出力先として残す
2. [ ] [ID: P5-PROGRESS-S2] `tools/gen_backend_progress.py` を作成する — `work/parity-results/*.json` を読み、fixture 一覧・sample 一覧と突き合わせて進捗ページを生成する。表示:
   - fixture parity マトリクス: 全ケース × 全言語。状態は 🟩 PASS / 🟥 FAIL / 🟨 TM (toolchain_missing) / 🟪 TO (timeout) / ⬜ 未実行
   - sample parity マトリクス: 同上
   - selfhost マトリクス: selfhost 言語 × emit 先言語。状態は ⬜ 未着手 / 🟨 emit OK / 🟧 build OK / 🟩 parity PASS
   - 古い結果（例: 7日以上前）には警告マークを付与
3. [ ] [ID: P5-PROGRESS-S3] 生成先を `docs/ja/language/backend-progress.md` とし、README.md からリンクする
4. [ ] [ID: P5-PROGRESS-S4] selfhost 結果の書き出し形式を定義する — `work/parity-results/selfhost_<lang>.json` に emit/build/parity の段階と成否を記録する

### P10-REORG: tools/ と test/unit/ の棚卸し・統合・管理台帳

文脈: [docs/ja/plans/p10-tools-test-reorg.md](../plans/p10-tools-test-reorg.md)

前提: P0〜P4 の主要タスクが全て落ち着いてから着手。

1. [ ] [ID: P10-REORG-S1] tools/ 全スクリプトの棚卸し
2. [ ] [ID: P10-REORG-S2] tools/check/, tools/gen/, tools/run/ にフォルダ分け
3. [ ] [ID: P10-REORG-S3] test/unit/ 全テストの棚卸し
4. [ ] [ID: P10-REORG-S4] test/unit/ → tools/unittest/ に統合・再編
5. [ ] [ID: P10-REORG-S5] 全パス参照の更新
6. [ ] [ID: P10-REORG-S6] tools/README.md 管理台帳を作成
7. [ ] [ID: P10-REORG-S7] CI で台帳突合チェックを追加
8. [ ] [ID: P10-REORG-S8] AGENTS.md にファイル追加禁止ルールを追加

### P10.5-MAPPING-VALIDATE: mapping.json 妥当性チェッカーの新設

仕様: [docs/ja/spec/spec-emitter-guide.md](../spec/spec-emitter-guide.md) §7.1〜7.3

1. [ ] [ID: P10.5-MAPVAL-S1] `tools/check_mapping_json.py` を作成する — 全言語の `src/runtime/<lang>/mapping.json` を対象に以下を検証する:
   - valid JSON であること
   - `calls` キーが存在すること
   - `builtin_prefix` が定義されていること
   - 必須エントリ（`env.target`）が `calls` に存在すること（spec-emitter-guide §7.3）
   - `calls` の値に空文字がないこと
2. [ ] [ID: P10.5-MAPVAL-S2] `tools/run_local_ci.py` に組み込む
3. [ ] [ID: P10.5-MAPVAL-S3] 既存の全 mapping.json に `env.target` エントリを追加する

### P11-VERSION-GATE: toolchain2 用バージョンチェッカーの新設

前提: toolchain2 への完全移行後に着手。

1. [ ] [ID: P11-VERGATE-S1] `src/toolchain2/` 向けの `transpiler_versions.json` を新設する（toolchain1 の `src/toolchain/misc/transpiler_versions.json` は廃止）
2. [ ] [ID: P11-VERGATE-S2] toolchain2 のディレクトリ構成に合わせた shared / 言語別の依存パスを定義する
3. [ ] [ID: P11-VERGATE-S3] バージョンチェッカーを新しく書く（PATCH 以上の bump で OK とする。MINOR/MAJOR はユーザーの明示指示がある場合のみ）
4. [ ] [ID: P11-VERGATE-S4] 旧チェッカー（`tools/check_transpiler_version_gate.py`）と旧バージョンファイルを廃止する

### P20-INT32: int のデフォルトサイズを int64 → int32 に変更

文脈: [docs/ja/plans/p4-int32-default.md](../plans/p4-int32-default.md)

前提: Go selfhost 完了後に着手。影響範囲が大きいため P4 → P20 に降格。

1. [ ] [ID: P20-INT32-S1] spec-east.md / spec-east2.md の `int` → `int32` 正規化ルール変更
2. [ ] [ID: P20-INT32-S2] resolve の型正規化を修正
3. [ ] [ID: P20-INT32-S3] sample 18 件のオーバーフロー確認 + 必要な箇所を `int64` に明示
4. [ ] [ID: P20-INT32-S4] golden 再生成 + 全 emitter parity 確認
