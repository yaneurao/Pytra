# TASK GROUP: TG-P1-RUNTIME-LAYOUT

最終更新: 2026-02-24

関連 TODO:
- `docs-ja/todo.md` の `ID: P0-RUNTIME-SEP-01`（`P0-RUNTIME-SEP-01-S1` 〜 `P0-RUNTIME-SEP-01-S5`）
- `docs-ja/todo.md` の `ID: P1-RUNTIME-01`（`P1-RUNTIME-01-S1` 〜 `P1-RUNTIME-01-S3`）
- `docs-ja/todo.md` の `ID: P1-RUNTIME-02`（`P1-RUNTIME-02-S1` 〜 `P1-RUNTIME-02-S2`）
- `docs-ja/todo.md` の `ID: P1-RUNTIME-03`（`P1-RUNTIME-03-S1` 〜 `P1-RUNTIME-03-S2`）
- `docs-ja/todo.md` の `ID: P1-RUNTIME-05`（`P1-RUNTIME-05-S1` 〜 `P1-RUNTIME-05-S3`）

背景:
- 言語ごとに runtime 配置規約が分断され、保守責務と探索規則が揺れている。
- C++ runtime では生成物と手書き実装が混在し、CI での責務検証が難しい。

目的:
- `src/runtime/<lang>/pytra/` へ配置規約を統一し、runtime 資産の責務境界を揃える。
- C++ runtime では生成層と手書き層を上位フォルダで分離し、将来の多言語展開で再利用可能な運用を確立する。

対象:
- C++: `src/runtime/cpp/pytra/` の「生成物 / 手書き / 入口フォワーダー」分離（`pytra-gen` / `pytra-core`）
- Rust: `src/rs_module/` から `src/runtime/rs/pytra/` への段階移行
- 他言語: `src/*_module/` 依存資産の `src/runtime/<lang>/pytra/` への移行計画
- `py2*` / hooks の解決パス統一

非対象:
- 各言語 runtime の機能追加そのもの

受け入れ基準:
- ランタイム参照先が `src/runtime/<lang>/pytra/` へ統一される。
- C++ runtime で `pytra-gen`（生成専用）と `pytra-core`（手書き専用）が CI で検証される。
- `src/*_module/` 直下への新規 runtime 追加が止まる。

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- 言語別 smoke tests（`test/unit/test_py2*_smoke.py`）

サブタスク実行順（todo 同期）:

1. `P0-RUNTIME-SEP-01`（C++ runtime 起源分離）
   - `P0-RUNTIME-SEP-01-S1`: `src/runtime/cpp/pytra/` の全ファイルを「生成物 / 手書き / 入口」に分類する（結果: `docs-ja/plans/p1-runtime-layout-unification-inventory.md`）。
   - `P0-RUNTIME-SEP-01-S2`: `src/runtime/cpp/pytra-gen/` と `src/runtime/cpp/pytra-core/` の最小構成を作る。
   - `P0-RUNTIME-SEP-01-S3`: 自動生成ファイルを `pytra-gen` へ段階移動する。
   - `P0-RUNTIME-SEP-01-S4`: 手書きファイル（`-impl` 含む）を `pytra-core` へ段階移動する。
   - `P0-RUNTIME-SEP-01-S5`: CI ガード（`AUTO-GENERATED` 必須/禁止）を導入する。
2. `P1-RUNTIME-01`（Rust 配置統一）
   - `P1-RUNTIME-01-S1`: `src/rs_module/` の責務マップを作る。
   - `P1-RUNTIME-01-S2`: `src/runtime/rs/pytra/` へ段階移動し、互換レイヤを維持する。
   - `P1-RUNTIME-01-S3`: 回帰確認後に `src/rs_module/` 依存を縮退する。
3. `P1-RUNTIME-02`（Rust 解決パス更新）
   - `P1-RUNTIME-02-S1`: `py2rs.py` / hooks の path 解決箇所と互換仕様を確定する。
   - `P1-RUNTIME-02-S2`: 新パスへ切り替え、旧パス fallback を撤去する。
4. `P1-RUNTIME-03`（`src/rs_module/` 廃止）
   - `P1-RUNTIME-03-S1`: 参照元を全件列挙し、廃止可否を確定する。
   - `P1-RUNTIME-03-S2`: 参照を置換し、`src/rs_module/` を削除する。
5. `P1-RUNTIME-05`（Rust 以外の解決パス統一）
   - `P1-RUNTIME-05-S1`: 言語ごとの現行 runtime 解決パス差分を棚卸しする。
   - `P1-RUNTIME-05-S2`: 各 `py2<lang>.py` / hooks の参照を新基準へ順次更新する。
   - `P1-RUNTIME-05-S3`: 多言語 smoke 実行後に旧パス互換レイヤを段階撤去する。

`P1-RUNTIME-02-S1` 棚卸し結果（Rust emitter/hooks の path 解決箇所と互換仕様）:

| 区分 | 実装箇所 | 現状 | 互換仕様（移行期間） |
|---|---|---|---|
| Rust import/use 変換 | `src/hooks/rs/emitter/rs_emitter.py::_module_id_to_rust_use_path` と `_collect_use_lines` | EAST `module_id` を Rust `use crate::...` パスへ機械変換 | 変換規則は維持しつつ、ランタイム実体は `src/runtime/rs/pytra/` 側を正本として扱う |
| CLI 側 runtime パス解決 | `src/py2rs.py` | `.py/.json -> EAST -> Rust` 変換のみ。`src/rs_module` 直接参照なし | `py2rs.py` には新旧パス fallback を持たせず、互換は runtime 側 shim で吸収する |
| 既存生成物の path 参照 | `sample/rs/*.rs`（`#[path = "../../src/runtime/rs/pytra/built_in/py_runtime.rs"]`） | 新パス参照へ切替済み | 過去生成物が旧参照でも `src/rs_module/py_runtime.rs` shim で互換維持する |

`P1-RUNTIME-03-S1` 棚卸し結果（`src/rs_module/` 参照元と廃止可否）:

| 参照元 | 参照内容 | 廃止可否判定 | 条件/備考 |
|---|---|---|---|
| `src/rs_module/py_runtime.rs` | 互換 shim 本体 | 削除済み（`P1-RUNTIME-03-S2`） | 旧参照 fallback を終了し削除 |
| `tools/check_rs_runtime_layout.py` | Rust runtime レイアウト検証 | 更新済み（`P1-RUNTIME-03-S2`） | `src/rs_module` ソース禁止 + `src/runtime/rs/pytra/` 必須を検証 |
| `docs-ja/how-to-use.md` / `docs/how-to-use.md` | `src/rs_module` を runtime 配置として案内 | `P1-RUNTIME-03-S2` で更新対象 | 新配置 `src/runtime/rs/pytra/` へ文言置換 |
| `docs-ja/plans/pytra-wip.md` / `docs/plans/pytra-wip.md` | 旧配置参照の移行注記 | `P1-RUNTIME-03-S2` で更新対象 | 旧配置記述を互換終了済みへ変更 |
| `docs-ja/spec/spec-dev.md` | `src/rs_module` を移行中として言及 | `P1-RUNTIME-03-S2` で更新対象 | 「非依存」の最終状態へ更新 |

`P1-RUNTIME-01-S1` 棚卸し結果（`src/rs_module/` -> `src/runtime/rs/pytra/` 対応表）:

- 現状 `src/rs_module/` は `py_runtime.rs` 1ファイルのみ（`find src/rs_module -type f` で確認）。
- `py_runtime.rs` は built-in / std / utils の責務が単一ファイルに混在しているため、`P1-RUNTIME-01-S2` で下記分割を行う。

| 現在 (`src/rs_module/py_runtime.rs`) の責務 | 代表シンボル | 移行先（予定） |
|---|---|---|
| Python組み込み互換（truthy/len/slice/in/print/文字判定） | `PyBool`, `PyLen`, `PySlice`, `py_bool`, `py_len`, `py_slice`, `py_in`, `py_print`, `py_isdigit`, `py_isalpha` | `src/runtime/rs/pytra/built_in/py_runtime.rs` |
| std.math 互換 | `math_sin`, `math_cos`, `math_tan`, `math_sqrt`, `math_exp`, `math_log`, `math_log10`, `math_fabs`, `math_floor`, `math_ceil`, `math_pow` | `src/runtime/rs/pytra/std/math.rs` |
| std.pathlib 互換 | `PyPath` と関連 impl | `src/runtime/rs/pytra/std/pathlib.rs` |
| std.time 互換 | `perf_counter` | `src/runtime/rs/pytra/std/time.rs` |
| utils.gif 互換 | `py_grayscale_palette`, `py_save_gif`, `gif_lzw_encode` | `src/runtime/rs/pytra/utils/gif.rs` |
| utils.png 互換 | `py_write_rgb_png`, `png_crc32`, `png_adler32`, `png_chunk` | `src/runtime/rs/pytra/utils/png.rs` |
| compiler 向け共通レイヤ | なし（今回棚卸し時点で `py_runtime.rs` 内に compiler 専用APIなし） | `src/runtime/rs/pytra/compiler/README.md`（空ディレクトリ維持） |

`P1-RUNTIME-05-S1` 棚卸し結果（Rust 以外 runtime 解決パス差分）:

- 前提確認:
  - `src/runtime/{cs,js,ts,go,java,kotlin,swift}/pytra/` は未作成（全言語 `missing`）。
  - 既存 runtime 実体は `src/{cs,js,ts,go,java,kotlin,swift}_module/` 配下に存在。
- 集計対象:
  - `src/py2{cs,js,ts,go,java,kotlin,swift}.py`
  - `src/hooks/{cs,js,ts,go,java,kotlin,swift}/`
  - 生成確認用: `sample/{cs,js,ts,go,java,kotlin,swift}/`
  - 連動箇所（S2 で同時更新が必要）: `src/common2/js_ts_native_transpiler.py`, `test/unit/test_py2js_smoke.py`, `test/unit/test_js_ts_runtime_dispatch.py`, `docs-ja/how-to-use.md`

| 言語 | runtime 実体（現行） | path 解決の実装箇所（現行） | 現行状態 | S2 の更新方針 |
|---|---|---|---|---|
| C# | `src/cs_module/{py_runtime.cs,pathlib.cs,png_helper.cs,gif_helper.cs,time.cs}` | `py2cs.py` は path 非依存。`cs_emitter.py` は import `module_id` を namespace 化し、生成コードは `Pytra.CsModule.*` を参照 | `src/runtime/cs/pytra/` 未整備 | runtime 実体を `src/runtime/cs/pytra/` へ移動し、namespace/参照名を新配置へ合わせる |
| JS | `src/js_module/{py_runtime.js,pathlib.js,png_helper.js,gif_helper.js,math.js,time.js}` | `src/hooks/js/emitter/js_emitter.py` が `require(__pytra_root + '/src/js_module/py_runtime.js')` を直書き | 旧パス固定参照が残存 | `js_emitter.py` の runtime require 基準を `src/runtime/js/pytra/` へ切替 |
| TS | `src/ts_module/{py_runtime.ts,pathlib.ts,png_helper.ts,gif_helper.ts,math.ts,time.ts}` | `py2ts.py` は `ts_emitter.py` 経由、`ts_emitter.py` は `js_emitter.py` を再利用（JS 側直書きに追従）。加えて `src/common2/js_ts_native_transpiler.py` が `src/ts_module/*.ts` を直書き | `js_module` と `ts_module` 参照が混在 | `ts_emitter` 経路と `common2` 経路の両方を `src/runtime/ts/pytra/` 基準へ統一 |
| Go | `src/go_module/py_runtime.go` | `py2go.py` / `go_emitter.py` は preview 出力で runtime パス解決なし | runtime 実体配置のみ旧規約 | `src/runtime/go/pytra/` 新設 + 将来 native emitter 切替時に同基準を使用 |
| Java | `src/java_module/PyRuntime.java` | `py2java.py` / `java_emitter.py` は preview 出力で runtime パス解決なし | runtime 実体配置のみ旧規約 | `src/runtime/java/pytra/` 新設 + 将来 native emitter 切替時に同基準を使用 |
| Kotlin | `src/kotlin_module/py_runtime.kt` | `py2kotlin.py` / `kotlin_emitter.py` は preview 出力で runtime パス解決なし | runtime 実体配置のみ旧規約 | `src/runtime/kotlin/pytra/` 新設 + 将来 native emitter 切替時に同基準を使用 |
| Swift | `src/swift_module/py_runtime.swift` | `py2swift.py` / `swift_emitter.py` は preview 出力で runtime パス解決なし | runtime 実体配置のみ旧規約 | `src/runtime/swift/pytra/` 新設 + 将来 native emitter 切替時に同基準を使用 |

`P1-RUNTIME-05-S1` の差分サマリ:

1. `py2<lang>.py` 本体に runtime path 直書きはない（CLI 層は path 非依存）。
2. 実コードで path 直書きがあるのは `JS/TS` 系（`js_emitter.py` と `common2/js_ts_native_transpiler.py`）。
3. `Go/Java/Kotlin/Swift` は preview backend のため path 解決処理が未実装で、先に runtime 配置規約の正本化が必要。
4. 既存テスト/ドキュメントは `src/js_module` と `src/*_module` 前提のものがあり、S2/S3 で同時更新対象になる。

運用ルール:

1. 新規 runtime 実装（`py_runtime.*`, `pathlib.*`, `png/gif helper` など）は `src/runtime/<lang>/pytra/` 配下にのみ追加する。
2. `src/*_module/` 直下は互換レイヤ専用とし、新規実体ファイルは追加しない。
3. 互換レイヤは「移行完了後に削除する前提」の暫定資産として扱い、`todo` に撤去タスクを必ず紐付ける。
4. 例外追加が必要な場合は、同一ターンで `docs-ja/todo.md` に理由と撤去期限を記録する。

決定ログ:
- 2026-02-22: 初版作成。
- 2026-02-22: Rust 以外（C#/JS/TS/Go/Java/Swift/Kotlin）の `src/*_module/` -> `src/runtime/<lang>/pytra/` 移行計画（資産マップ + 段階手順）を追加。
- 2026-02-22: `src/*_module/` 直下に新規 runtime 実体を追加しない運用ルールを明文化。
- 2026-02-23: docs-ja/todo.md の親子 ID 分割（-S*）へ同期し、P0-RUNTIME-SEP-01 を含む実行順を明示した。
- 2026-02-23: `P0-RUNTIME-SEP-01-S1` を実施し、`src/runtime/cpp/pytra/` 全57ファイルの分類台帳を `docs-ja/plans/p1-runtime-layout-unification-inventory.md` として追加した（`generated=38`, `handwritten=19`, `entry_forwarder=0`）。
- 2026-02-23: `P0-RUNTIME-SEP-01-S2` を実施し、`src/runtime/cpp/pytra-gen/` と `src/runtime/cpp/pytra-core/` を新設した。両ディレクトリに `README.md` を配置し、責務境界（生成専用/手書き専用）と禁止事項を固定した。
- 2026-02-23: `P0-RUNTIME-SEP-01-S3` を実施し、生成物38ファイルを `src/runtime/cpp/pytra-gen/` へ移動した。`src/runtime/cpp/pytra/` 側には同名フォワーダー（`.h/.cpp`）を配置して既存ビルド参照を互換維持した。合わせて `src/py2cpp.py --emit-runtime-cpp` は `pytra-gen` へ出力し、`pytra/` 側フォワーダーを自動更新するよう変更した。
- 2026-02-23: `P0-RUNTIME-SEP-01-S4` を実施し、手書き19ファイル（`built_in/*`, `std/*-impl.*`）を `src/runtime/cpp/pytra-core/` へ移動した。これにより `src/runtime/cpp/pytra/` は全57ファイルが公開フォワーダー層となり、実体は `pytra-gen`（生成）と `pytra-core`（手書き）へ分離された。
- 2026-02-23: `P0-RUNTIME-SEP-01-S5` を実施し、`tools/check_runtime_cpp_layout.py` を追加した。`pytra-gen` は `AUTO-GENERATED FILE. DO NOT EDIT.` 必須、`pytra-core` は同マーカー禁止を検証し、`tools/run_local_ci.py` に組み込んで常時ガード化した。
- 2026-02-24: `P1-RUNTIME-01-S1` として `src/rs_module/` の棚卸しを実施し、`py_runtime.rs` に混在している責務を `src/runtime/rs/pytra/{built_in,std,utils,compiler}` へ分割する対応表を本ファイルへ追加した。
- 2026-02-24: `P1-RUNTIME-01-S2` として `src/runtime/rs/pytra/` 配下（`built_in/std/utils/compiler`）を新設し、`src/rs_module/py_runtime.rs` の実体を `src/runtime/rs/pytra/built_in/py_runtime.rs` へ移動した。`src/rs_module/py_runtime.rs` は `include!(\"../runtime/rs/pytra/built_in/py_runtime.rs\")` の互換 shim へ置換し、既存 `#[path = \"../../src/rs_module/py_runtime.rs\"]` 参照を維持したまま新配置を正本化した。`python3 tools/check_py2rs_transpile.py`（`checked=131 ok=131 fail=0 skipped=6`）で回帰がないことを確認した。
- 2026-02-24: ID: P1-RUNTIME-01-S3 として `src/rs_module` 依存縮退の固定化を実施した。`tools/check_rs_runtime_layout.py` を追加し、`src/rs_module/` 直下は互換 shim (`py_runtime.rs`) のみ許可、実体は `src/runtime/rs/pytra/built_in/py_runtime.rs` 必須とするガードを導入した。`tools/run_local_ci.py` に同チェックを組み込み、`python3 tools/check_py2rs_transpile.py`（`checked=131 ok=131 fail=0 skipped=6`）で回帰なしを確認した。
- 2026-02-24: ID: P1-RUNTIME-01（親タスク）を完了として履歴へ移管した。残作業は `P1-RUNTIME-02` 以降（参照パス切替と `src/rs_module` 最終撤去）へ移行する。
- 2026-02-24: ID: P1-RUNTIME-02-S1 として Rust path 解決箇所を棚卸しした。`py2rs.py` は runtime パス非依存、`rs_emitter.py` は `module_id -> use crate::...` の変換責務、既存生成物の旧 `src/rs_module` 参照は shim で吸収する互換方針を確定した。
- 2026-02-24: ID: P1-RUNTIME-02-S2 として生成物参照先を新パスへ切替した。`sample/rs/*.rs` の `#[path = "../../src/rs_module/py_runtime.rs"]` を `#[path = "../../src/runtime/rs/pytra/built_in/py_runtime.rs"]` へ一括更新し、コード側の旧パス依存を撤去した。旧参照 fallback は `src/rs_module/py_runtime.rs` shim のみ維持する。
- 2026-02-24: ID: P1-RUNTIME-02（親タスク）を完了として履歴へ移管した。次段は `P1-RUNTIME-03`（`src/rs_module` 廃止）へ進む。
- 2026-02-24: ID: P1-RUNTIME-03-S1 として `src/rs_module` 参照元を全件棚卸しし、コード側は `src/rs_module/py_runtime.rs` shim と `tools/check_rs_runtime_layout.py` のみが直接依存、残りは docs 記述であることを確認した。`P1-RUNTIME-03-S2` では shim 削除 + ガード更新 + docs 置換を同時実施する方針を確定した。
- 2026-02-24: ID: P1-RUNTIME-03-S2 として `src/rs_module/py_runtime.rs` を削除し、`tools/check_rs_runtime_layout.py` を「`src/rs_module` ソース禁止」ルールへ更新した。`docs-ja/how-to-use.md`、`docs-ja/spec/spec-dev.md`、`docs-ja/plans/pytra-wip.md` の旧参照を `src/runtime/rs/pytra/` 基準へ置換した。
- 2026-02-24: ID: P1-RUNTIME-03（親タスク）を完了として履歴へ移管した。Rust runtime の旧配置依存は解消し、残タスクは `P1-RUNTIME-05`（他言語統一）へ移行する。
- 2026-02-24: ID: `P1-RUNTIME-05-S1` として Rust 以外（`cs/js/ts/go/java/kotlin/swift`）の runtime 解決パスを棚卸しした。`py2<lang>.py` 本体は path 非依存、直書き参照は `src/hooks/js/emitter/js_emitter.py` と `src/common2/js_ts_native_transpiler.py` に集中すること、`Go/Java/Kotlin/Swift` は preview backend のため path 解決実装未着手であることを確定した。
