# P2: 多言語 runtime の C++ 同等化（API 契約・機能カバレッジ統一）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-RUNTIME-PARITY-CPP-01`

背景:
- C++ runtime は `built_in/std/utils` で機能が分割され、`math/time/json/pathlib/random/re/sys/...` まで比較的広く実装されている。
- 他言語 runtime は `py_runtime` 単体中心の言語が多く、C++ と同等の API 面/機能面カバレッジに達していない。
- 既存 P1（runtime 外出し）は「inline helper 撤去」が目的であり、C++ 同等機能までを保証する計画ではない。

目的:
- 「C++ runtime を仕様の正」として、他言語 runtime の API 契約と機能カバレッジを段階的に揃える。
- backend ごとの差分を吸収する adapter 層を整備し、生成コード側は言語差を意識せず同等 API を呼べる状態にする。

対象:
- `src/runtime/{cs,go,java,js,ts,kotlin,swift,ruby,lua,scala,php,rs}/`
- 必要な `src/backends/<lang>/emitter/*` の runtime 呼び出し面
- parity 検証スクリプトと runtime 契約テスト

非対象:
- C++ runtime 自体の大規模再設計
- EAST 仕様変更
- すべての標準ライブラリを一度に完全移植（段階導入）

受け入れ基準:
- C++ runtime の「必須 API セット」に対して、各言語 runtime の実装有無が一覧化される。
- 最低限の共通 API（`math/time/pathlib/json/png/gif` + core helper）について、各言語で同名または adapter 経由で同等契約を満たす。
- `sample`/`test` の parity 検証で runtime 差由来 fail を段階的に削減できる。
- runtime 差分を追跡する回帰チェック（欠落 API 検知）が追加される。

実施方針:
1. C++ runtime を基準に「必須 API カタログ」を確定する。
2. 各言語 runtime の実装マップを作成し、欠落・挙動差を分類する。
3. 欠落が多い領域（`math/time/pathlib/json` など）から順に埋める。
4. emitter 側は言語固有呼び出しを adapter へ寄せ、API 名の揺れを縮退する。
5. 機能追加ごとに parity/回帰を固定する。

優先導入順（推奨）:
- Wave 1: `go/java/kotlin/swift`（単一 runtime 依存が強く、差分吸収効果が高い）
- Wave 2: `ruby/lua/scala/php`
- Wave 3: `js/ts/cs/rs`（既存実装は比較的進んでいるため不足分の穴埋め）

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/runtime_parity_check.py --case-root sample --all-samples --ignore-unstable-stdout`
- 言語別 `check_py2*.py`（対象 backend）

## 分解

- [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-01] C++ runtime の必須 API カタログ（module/function/契約）を抽出し、正本一覧を作成する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S1-02] 各言語 runtime の実装有無マトリクスを作成し、欠落/互換/挙動差を分類する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S1-03] 同等化対象を `Must/Should/Optional` の3段階で優先度付けする。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1（`go/java/kotlin/swift`）で `math/time/pathlib/json` の不足 API を実装・統一する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-02] Wave1 の emitter 呼び出しを adapter 経由へ寄せ、API 名揺れを吸収する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-03] Wave1 の parity 回帰を追加し、runtime 差由来 fail を固定する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-01] Wave2（`ruby/lua/scala/php`）で同様に不足 API を実装・統一する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-02] Wave2 の emitter 呼び出しを adapter 経由へ寄せる。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-03] Wave2 の parity 回帰を追加し、runtime 差由来 fail を固定する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-01] Wave3（`js/ts/cs/rs`）で不足 API を補完し、契約差を解消する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-02] runtime API 欠落検知チェックを追加し、CI/ローカル回帰へ組み込む。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-03] `docs/ja/spec` / `docs/en/spec` に runtime 同等化ポリシーと進捗表を反映する。

決定ログ:
- 2026-03-02: ユーザー要望により、runtime 外出し（P1）とは別軸で「C++ 同等機能」を目的とする P2 計画を起票。
- 2026-03-02: 「実装行数の一致」ではなく「API 契約・挙動同等」を完了判定に採用。
- 2026-03-03: [ID: P2-RUNTIME-PARITY-CPP-01-S1-01] `docs/ja/spec/spec-runtime.md` に C++ runtime 正本カタログ（core/math/time/pathlib/json/png/gif + timeit/random）を追加し、Wave の基準 API を固定。

## S1-01 実装（2026-03-03）

- 反映先: `docs/ja/spec/spec-runtime.md` セクション「0. C++ runtime API 正本カタログ」。
- 抽出結果:
  - `Must`: `built_in/core`, `std/math`, `std/time`, `std/pathlib::Path`, `std/json`, `utils/png`, `utils/gif`
  - `Should`: `std/timeit`, `std/random`
- 正本パスを `pytra-core` / `pytra-gen` に固定し、`pytra/*` を forwarder 層として明記。
