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
- [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-02] 各言語 runtime の実装有無マトリクスを作成し、欠落/互換/挙動差を分類する。
- [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-03] 同等化対象を `Must/Should/Optional` の3段階で優先度付けする。
- [x] [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1（`go/java/kotlin/swift`）で `math/time/pathlib/json` の不足 API を実装・統一する。
- [x] [ID: P2-RUNTIME-PARITY-CPP-01-S2-01-S1-01] Wave1-Go: `json.loads/dumps` runtime API を追加し、Go emitter の `json.*` 呼び出しを runtime helper へ統一する。
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
- 2026-03-03: [ID: P2-RUNTIME-PARITY-CPP-01-S1-02] `src/runtime/<lang>/pytra` を棚卸しし、`native/mono/compat/missing` 分類の実装有無マトリクスと主要ギャップ（json/pathlib/gif/分離構成差）を確定。
- 2026-03-03: [ID: P2-RUNTIME-PARITY-CPP-01-S1-03] マトリクス結果を `Must/Should/Optional` へ優先度化し、Wave1/2/3 の実装順を固定。
- 2026-03-04: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01-S1-01] Go runtime に `pyJsonLoads/pyJsonDumps` を実装（`encoding/json` + number preserving decode）し、Go emitter で `json.loads/json.dumps` を runtime helper へマップ。`test_py2go_smoke.py` と `check_py2go_transpile.py` の通過を確認。
- 2026-03-04: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1-Java: `PyRuntime` に `pyJsonLoads/pyJsonDumps`（再帰JSON parser/stringify）を追加し、Java emitter の `json.loads/json.dumps` を runtime helper 経由へ統一。`test_py2java_smoke.py` と `check_py2java_transpile.py` で回帰なしを確認。
- 2026-03-04: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1-Kotlin: `py_runtime.kt` に `pyJsonLoads/pyJsonDumps`（再帰JSON parser/stringify）を追加し、Kotlin emitter の `json.loads/json.dumps` を helper 経由へ統一。`test_py2kotlin_smoke.py` と `check_py2kotlin_transpile.py` を通過。
- 2026-03-04: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1-Swift: `py_runtime.swift` に `pyJsonLoads/pyJsonDumps`（`JSONSerialization` + 互換型変換）を追加し、Swift emitter の `json.loads/json.dumps` を helper 経由へ統一。`test_py2swift_smoke.py` と `check_py2swift_transpile.py` を通過。
- 2026-03-04: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1-Java: `Path` を `PyRuntime.Path` として runtime に実装（`parent/name/stem` + `exists/read_text/write_text/mkdir/resolve`）し、Java emitter の型/ctor/isinstance を `PyRuntime.Path` へ統一。`test_py2java_smoke.py` と `check_py2java_transpile.py` を通過。
- 2026-03-04: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1-Kotlin/Swift: runtime に `Path` クラス（`parent/name/stem` + `exists/read_text/write_text/mkdir/resolve`）を追加し、既存 emitter の `Path(...)` 出力がコンパイル可能になることを `test_py2{kotlin,swift}_smoke.py`・`check_py2{kotlin,swift}_transpile.py` で確認。
- 2026-03-04: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1-Go: runtime に `Path` wrapper（`NewPath/__pytra_as_Path` + method群）を追加し、Go emitter で call keyword 値を一般呼び出しへ反映（`mkdir(parents=True, exist_ok=True)` が `mkdir(true, true)` へ降りる）する修正を適用。`test_py2go_smoke.py` と `check_py2go_transpile.py` を通過。
- 2026-03-04: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1-Kotlin/Swift: runtime に `pyMath*`（`sqrt/sin/cos/tan/exp/log/fabs/floor/ceil/pow/pi/e`）API を追加し、emitter の `math.*` 呼び出しを runtime helper 経由へ切替。`test_py2{kotlin,swift}_smoke.py` と `check_py2{kotlin,swift}_transpile.py` を通過。
- 2026-03-04: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1（`go/java/kotlin/swift`）の `math/time/pathlib/json` 不足 API 実装を完了し、`test_py2{go,java,kotlin,swift}_smoke.py` と `check_py2{go,java,kotlin,swift}_transpile.py` を green で固定。
- 2026-03-04: [ID: P2-RUNTIME-PARITY-CPP-01-S2-02] Wave1 adapter 化の先行実装として、Go/Java emitter の `math.*` 呼び出しを runtime helper (`pyMath*`) 経由へ統一。Go 側は `math` import 依存を emitter から除去し、`test_py2{go,java}_smoke.py` と `check_py2{go,java}_transpile.py` で非退行確認。

## S1-01 実装（2026-03-03）

- 反映先: `docs/ja/spec/spec-runtime.md` セクション「0. C++ runtime API 正本カタログ」。
- 抽出結果:
  - `Must`: `built_in/core`, `std/math`, `std/time`, `std/pathlib::Path`, `std/json`, `utils/png`, `utils/gif`
  - `Should`: `std/timeit`, `std/random`
- 正本パスを `pytra-core` / `pytra-gen` に固定し、`pytra/*` を forwarder 層として明記。

## S1-02 実装（2026-03-03）

判定キー:
- `native`: 専用モジュール/名前空間として分離実装あり
- `mono`: 単一 `py_runtime.*` 内に実装あり
- `compat`: 言語標準 API へ直結（専用 runtime API なし）
- `missing`: 実装未確認（呼び出し時は不足/代替挙動の可能性）

| lang | core helper | math | time | pathlib | json | png | gif | 備考 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `cs` | mono | native | native | native | native | native | native | C++基準に最も近い分離構成。 |
| `js` | mono | native | native | native | compat | native | native | `json` は専用 runtime なし（JS `JSON.*` 依存）。 |
| `ts` | mono | native | native | native | compat | native | native | JS と同系統。 |
| `go` | mono | mono | mono | mono | missing | mono | mono | 単一 `py_runtime.go` へ集中。 |
| `java` | mono | mono | mono | mono | missing | mono | mono | 単一 `PyRuntime.java` へ集中。 |
| `kotlin` | mono | missing | mono | missing | missing | mono | missing | 画像は PNG のみ確認。 |
| `swift` | mono | missing | mono | missing | missing | mono | missing | 画像は PNG のみ確認。 |
| `ruby` | mono | missing | mono | missing | missing | mono | mono | 単一 `py_runtime.rb`。 |
| `lua` | mono | mono | mono | mono | missing | mono | mono | path/gif/png は monolithic helper。 |
| `scala` | mono | compat | mono | mono | missing | mono | mono | math は言語標準利用中心。 |
| `php` | mono | missing | native | missing | compat | native | native | `json_encode` 利用はあるが `loads/dumps` 契約不足。 |
| `rs` | mono | mono | mono | mono | missing | mono | mono | `built_in/py_runtime.rs` に集約。 |
| `nim` | mono | missing | mono | missing | missing | mono | missing | 現状は最小 runtime。 |

欠落/互換/挙動差の主分類:
1. `json` 欠落: `cs` 以外で C++ `loads/dumps` 契約と同名 API が不足（`js/ts/php` は標準 API 依存の compat）。
2. `pathlib` 欠落: `kotlin/swift/ruby/php/nim` は C++ `Path` の最小 API 群に未到達。
3. 画像 API 偏在: `kotlin/swift/nim` で `gif` 側が不足（`png` のみ）。
4. 実装形態差: `go/java/rs/lua/scala/ruby` は monolithic runtime 集中で、`cs/js/ts` の分離構成と乖離。

## S1-03 実装（2026-03-03）

### Must（Wave1/2 先行）

1. `json.loads/dumps` を `go/java/kotlin/swift/ruby/lua/scala/php/rs/nim` へ追加し、C++ 公開契約に合わせる。
2. `pathlib.Path` 最小 API（`resolve/parent/name/stem/exists/mkdir/read_text/write_text`）を `kotlin/swift/ruby/php/nim` に追加する。
3. `gif` API（`grayscale_palette/save_gif`）を `kotlin/swift/nim` に追加する。
4. `math/time/pathlib/json/png/gif` の emitter 呼び出しを adapter 経由へ寄せ、名前揺れを吸収する。

### Should（Wave2/3）

1. monolithic 実装（`go/java/rs/lua/scala/ruby`）を `std/*` / `utils/*` 分離へ段階移行する。
2. `timeit/random` の C++ 同等 API を不足言語へ補完する。
3. `js/ts/php` の `json` compat 経路を専用 runtime API 名へ揃える。

### Optional（後段）

1. API 名一致後の挙動差（例外文言/誤差許容）を厳密化する。
2. module 分離後の runtime 配置最適化（`profiles` と合わせた責務整理）を行う。
3. parity 失敗時の runtime 欠落自動診断を `tools/` に追加する。
