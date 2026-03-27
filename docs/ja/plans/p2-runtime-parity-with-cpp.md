<a href="../../en/plans/p2-runtime-parity-with-cpp.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: 多言語 runtime の C++ 同等化（再設計版: SoT厳守 + 生成優先）

最終更新: 2026-03-05

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-RUNTIME-PARITY-CPP-02`

背景:
- 旧P2（`P2-RUNTIME-PARITY-CPP-01`）は「同等化」を急ぐあまり、runtime 実装責務と生成責務の境界が曖昧になり、実装方針に誤りが混入した。
- 具体的には、pure Python 正本からの機械生成を優先すべき箇所で、言語別に手書き実装・特別命名・monolithic 埋め込みが発生しやすい状態だった。
- また、emitter がライブラリ関数名を文字列比較で直接分岐する経路が残り、IR 解決責務の逸脱が再発した。

目的:
- C++ runtime との API 契約同等化を維持しつつ、実装方法を「SoT厳守」「生成優先」「責務分離」に再定義する。
- runtime 同等化を、設計ルール + 静的ガード + parity 回帰で再発不能な形へ固定する。

対象:
- `src/runtime/<lang>/{pytra-core,pytra-gen}/`
- `src/pytra/{std,utils}/`（正本モジュール）
- `src/toolchain/emit/*/emitter/*.py`（runtime 呼び出し経路）
- `tools/`（監査・生成・parity・CI導線）

非対象:
- C++ runtime 自体の大規模再設計
- EAST 仕様全面刷新
- 一括全言語移行（段階導入）

## 注意事項（必読）

以下は「推奨」ではなく必須ルール:

1. `src/pytra/std/*` / `src/pytra/utils/*` の pure Python 実装は正本（SoT）とし、対応機能を他言語で手書き再実装しない。
2. SoT 由来コードは必ず `src/runtime/<lang>/pytra-gen/` に配置し、`pytra-core` へ混在させない。
3. SoT 由来ファイル名は機械的素通し命名（例: `png.py -> png.<ext>`, `gif.py -> gif.<ext>`）を原則とし、helper 名の特別命名を禁止する。
4. `pytra-core` には言語依存の基盤処理のみを置く。SoT で表現可能な API は `pytra-gen` へ寄せる。
5. emitter で `callee_name == "..."` / `attr_name == "..."` による `pytra.std.*` / `pytra.utils.*` 関数名の直書き分岐を禁止する。
6. runtime/stdlib 呼び出しの解決責務は lower/IR 側に置く。emitter は解決済みノード（`runtime_call` 系）を描画するだけに限定する。
7. compiler/backends で Python 標準 `ast` モジュールに依存しない（selfhost 制約）。
8. `pytra-gen` の生成物には `source:` と `generated-by:` marker を必須化し、監査で fail-fast する。
9. parity 実行前に artifact を必ず掃除し、stdout だけでなく artifact サイズ/CRC32 も検証する。

## 受け入れ基準

- 旧P2（`P2-RUNTIME-PARITY-CPP-01`）は TODO 未完了一覧から除去され、新IDへ置換されている。
- 新P2の実施に必要な禁止事項が文書化され、検査可能な形（スクリプト/CI）で管理される。
- `pytra-gen` の命名・配置・marker に関する監査が全対象言語で通る。
- 非C++ emitter の runtime 呼び出し経路で、ライブラリ関数名直書き分岐が段階撤去される。
- parity 回帰（artifact サイズ/CRC32 含む）で runtime 差由来 fail が追跡可能になる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/audit_image_runtime_sot.py --fail-on-core-mix --fail-on-gen-markers --fail-on-non-compliant`
- `python3 tools/check_emitter_runtimecall_guardrails.py`
- `python3 tools/runtime_parity_check.py --case-root sample --all-samples --ignore-unstable-stdout`

## 分解

- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S1-01] 旧P2（`P2-RUNTIME-PARITY-CPP-01`）を TODO 未完了一覧から削除し、新P2へ置換する。
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S1-02] SoT/pytra-core/pytra-gen の責務境界を `docs/ja/spec` に追記し、禁止事項を固定する。
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S1-03] 対象モジュール（`std/utils`）の「生成必須 / core許可」分類表を作成する。
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S2-01] `pytra-gen` 命名規約（素通し命名）違反を検知する静的チェックを追加する。
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S2-02] SoT marker（`source/generated-by`）と配置違反（core混在）チェックを強化し、CIへ統合する。
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S2-03] `pytra-core` 内の SoT 再実装痕跡を棚卸しし、`pytra-gen` 移管計画へ反映する。
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S3-01] Java を先行対象として、runtime API 呼び出しを IR 解決経路へ統一（emitter 直書き撤去）する。
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S3-02] Java 以外の非C++ backend（`cs/js/ts/go/rs/swift/kotlin/ruby/lua/scala/php/nim`）へ同方針を展開する。
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S3-03] emitter 禁止ルール（ライブラリ名直書き）を lint 化し、PR/CI で fail-fast する。
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S4-01] 全対象言語で sample parity（artifact size+CRC32）を再実施し、差分を固定する。
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S4-02] ルール違反の再発時に即検知できる運用手順（ローカル/CI）を `docs/ja/how-to-use` と `docs/en/how-to-use` に反映する。

## S2-03 棚卸し結果（2026-03-05）

生ログ: `work/logs/runtime_core_sot_reimpl_inventory_20260305_s2_03.tsv`

| 言語 | 再実装痕跡ファイル（pytra-core） | 痕跡カテゴリ | 移管方針 |
| --- | --- | --- | --- |
| `cs` | `src/runtime/cs/pytra-core/std/json.cs` | JSON 実装本体 | `src/pytra/std/json.py` 正本から `pytra-gen/std/json.cs` 生成へ移行し、core 側は薄い adapter のみ許可。 |
| `go` | `src/runtime/go/pytra-core/built_in/py_runtime.go` | JSON + 画像 helper stub | JSON は `pytra-gen/std/json.go` へ移管、画像 helper は `pytra-gen/utils/{png,gif}.go` への委譲のみに縮退。 |
| `kotlin` | `src/runtime/kotlin/pytra-core/built_in/py_runtime.kt` | JSON 実装本体 | `pytra-gen/std/json.kt` を導入し、core 側 JSON 実装を撤去。 |
| `lua` | `src/runtime/lua/pytra-core/built_in/py_runtime.lua` | JSON 実装本体 | `pytra-gen/std/json.lua` 生成へ移行し、core から JSON encode/decode を除去。 |
| `php` | `src/runtime/php/pytra-core/py_runtime.php` | JSON 実装 + legacy include | `pytra-gen/std/json.php` 生成へ移行し、`py_runtime.php` は委譲のみ保持。 |
| `ruby` | `src/runtime/ruby/pytra-core/built_in/py_runtime.rb` | JSON wrapper | `pytra-gen/std/json.rb` を導入し、core 側 API は forwarder に統一。 |
| `scala` | `src/runtime/scala/pytra-core/built_in/py_runtime.scala` | JSON 実装本体 | `pytra-gen/std/json.scala` を生成し、core 側実装を撤去。 |
| `swift` | `src/runtime/swift/pytra-core/built_in/py_runtime.swift` | JSON 実装本体 | `pytra-gen/std/json.swift` を生成し、core 側は adapter 化。 |
| `rs` | `src/runtime/rs/pytra-core/built_in/py_runtime.rs` | 画像 marker 混在 + 画像 export | 画像 marker/再輸出を `pytra-gen/utils` 側へ一本化し、core の marker 混在を解消（allowlist 1件の縮退対象）。 |
| `cpp` | `src/runtime/cpp/pytra-core/built_in/py_runtime.h`（`re.sub` コメント） | 偽陽性（実装痕跡なし） | 棚卸し対象外。正規表現由来コメントのみで SoT 再実装ではないことを確認。 |

移管ウェーブ:

1. Wave-A（JSON系）: `cs/go/kotlin/lua/php/ruby/scala/swift` の JSON 実装を `pytra-gen/std/json.<ext>` へ寄せる。
2. Wave-B（画像系）: `rs/go` の core 側画像痕跡を `pytra-gen/utils/{png,gif}` 委譲へ縮退し、marker 混在を解消する。
3. Wave-C（監査収束）: allowlist（`runtime_core_gen_markers` / `runtime_pytra_gen_naming`）を段階削減し、`S4-01` parity で差分固定する。

決定ログ:
- 2026-03-05: ユーザー指示により、旧P2を破棄し、SoT厳守・生成優先・責務分離を前提とする再設計版へ置換した。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S1-01`] 旧P2の未完了残置（`docs/en/todo/index.md` / `docs/en/plans/p2-runtime-parity-with-cpp.md`）を新P2構成へ置換し、旧IDの未完了一覧参照を解消した。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S1-02`] `docs/ja/spec/spec-runtime.md` に「SoT / pytra-core / pytra-gen の責務境界」節を追加し、全言語共通の必須事項（生成優先、marker 必須、EAST3 解決済み描画）と禁止事項（core 再実装、特別命名、emitter 直書き分岐）を明文化。あわせて監査コマンドを固定した。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S1-03`] `docs/ja/spec/spec-runtime.md` に `std/utils` 分類表を追記し、`argparse..typing` と `assertions/gif/png` を生成必須、`dataclasses_impl/math_impl/time_impl` を `pytra-core` 許可（impl境界）として明示した。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S2-01`] `tools/check_runtime_pytra_gen_naming.py` を追加し、`pytra-gen` 配下の `std|utils` 素通し命名/配置違反を静的検出可能にした。既存負債は `tools/runtime_pytra_gen_naming_allowlist.txt`（11件）で明示し、`test/unit/tooling/test_check_runtime_pytra_gen_naming.py` と本体チェックの通過を確認した。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S2-02`] `tools/check_runtime_core_gen_markers.py` を追加し、全言語 `pytra-gen` の `source/generated-by` marker 必須と `pytra-core` への generated marker 混在禁止を静的監査化。`tools/run_local_ci.py` へ `check_runtime_core_gen_markers.py` と `check_runtime_pytra_gen_naming.py` を組み込み、`test_check_runtime_core_gen_markers.py` / `test_check_runtime_pytra_gen_naming.py` と本体チェックの通過を確認した。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S2-03`] `work/logs/runtime_core_sot_reimpl_inventory_20260305_s2_03.tsv` で `pytra-core` 再実装痕跡を棚卸し（10ファイル）。JSON系（8言語）と画像系（`rs/go`）へ分類し、`pytra-gen` 移管の Wave-A/B/C を計画へ反映した。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S3-01`] Java 先行移行の再監査として `check_emitter_runtimecall_guardrails.py`（strict backend=`java`）と `test_py2java_smoke.py`（25件）を実行し、直書き runtime 分岐の再流入がないことを確認。`_render_resolved_runtime_call` 経路と `resolved_runtime_call` 契約を維持しているため `S3-01` を完了扱いへ更新した。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S3-02`] 非Java backend 展開の再検証として `check_emitter_runtimecall_guardrails.py`（全backend no findings）と `test_py2{rs,rb,lua,scala,swift,ts}_smoke.py`（127件）を再通過。あわせて本ターンで実施済み `go/php/kotlin/js/nim/cs` smoke（117件）を合算し、対象 12 backend で IR解決経路 + fail-closed 方針の非退行を確認した。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S3-03`] lint/fail-fast 導線として `check_emitter_runtimecall_guardrails.py` と `check_emitter_forbidden_runtime_symbols.py` が `tools/run_local_ci.py` 必須ステップで常時実行されることを再確認。strict backend（`java`）は allowlist 非依存で即 fail するため、PR/CI 上の禁止ルールを固定できる状態にした。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] sample parity 再実行を開始し、`01_mandelbrot` と `02_raytrace_spheres` の全14target結果を `work/logs/runtime_parity_sample01_multilang_20260305.json` / `work/logs/runtime_parity_sample02_multilang_20260305.json` に固定。主要failカテゴリは `js/ts: png runtime export mismatch`, `go: generated png/gif compile errors + main衝突`, `nim: module名(先頭数字)不正`, `cpp(02): gif/png object link main重複 + write_rgb_png未解決`, `java(02): math.java class/file名不一致`。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] `nim` の `run_failed`（invalid module name）を修正。`pytra_cli_profiles.py` で nim 出力名を `main.nim` 固定化し、`runtime_parity_check.py` で nim 実行出力の `stderr` フォールバック + warning除外を追加。`01_mandelbrot` / `02_raytrace_spheres` の nim parity は artifact size+CRC32 一致で通過（`work/logs/runtime_parity_sample0{1,2}_nim_after_stderr_fallback_20260305.json`）。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] `runtime_parity_check.py --case-root sample --targets cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua,scala,php,nim --all-samples --ignore-unstable-stdout` を再実行し、`01` で `js/ts/go/nim`、`02/03` で追加の `java/cpp` 失敗を確認。主因は `js/png.js` の f-string 残存、`go/png.go` 文字列生成崩れ、Nim 実行モジュール名制約、Java runtime class 命名崩れ（`tmp`）、C++ runtime 側の `main` 重複 + `write_rgb_png` 未解決。`rs/cs/ruby/lua/php/swift/kotlin/scala` は少なくとも `01-03` で artifact size/CRC32 一致を確認。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] `src/pytra/utils/png.py` の SoT 実装を backend 互換寄り（f-string 除去、`bytes([..])` 置換）へ正規化し、`gen_runtime_from_manifest.py --items utils/png --targets js,ts,go` で再生成。`01_mandelbrot` の再検証で `js/ts` は構文エラーから「`write_rgb_png` export未解決」へ前進、`go` は文字列崩れが解消した一方で `extend/main重複/pyWriteRGBPNG未定義` が残ることを確認した。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] `runtime_parity_check.py` に target別出力ディレクトリの事前削除（stale transpile/build生成物の掃除）を追加し、再実行時の `work/transpile/*` 取り違えを解消。`runtime_parity_check.py --case-root sample --targets js,ts,go,cpp,java,nim 01_mandelbrot 02_raytrace_spheres` を再実行し、6target 全てで artifact size/CRC32 一致（`work/logs/runtime_parity_sample01_02_focus_20260305_after_freshfix.json`）を確認した。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] C++先行移行時に退避していた非C++ runtime を `src/runtime2/{rs,cs,js,ts,go,java,swift,kotlin,ruby,lua,scala,php,nim}` から `src/runtime/` へ復旧し、`backend_registry` runtime hook の `runtime source not found` 連鎖を解消した。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] PHP で `write_rgb_png/save_gif` が不一致だったため、`php_native_emitter` の `resolved_runtime_call`（単一シンボルのみ raw 名採用）を修正し、`gen_runtime_from_manifest.py` の PHP postprocess に `_*_append_list(&$dst, ...)` 参照渡し化を追加。`runtime/php/pytra-core/py_runtime.php` に `open`/`PyFile`/bytes変換を補強して `sample/01,02` の 14target parity（artifact size+CRC32）一致を確認（`work/logs/runtime_parity_sample01_02_all_targets_after_php_runtime_fixes_20260305.json`）。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] Nim の残差分として `save_gif` の戻り値 `int`（式文未discardエラー）と `math.pi`（`PI` への正規化不足）を修正。`nim_native_emitter.py` と `runtime/nim/{pytra,pytra-gen}/utils` を更新し、`runtime_parity_check.py` で `04,05,06` の 14target parity（artifact size+CRC32）一致を確認（`work/logs/runtime_parity_sample04_06_all_targets_after_nim_fix_20260305.json`）。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] `07-09` で Lua artifact mismatch を確認し、`lua_native_emitter.py` の `IfExp` を `__pytra_truthy` ベース遅延評価へ修正。再実行で `07/08/09` の 14target artifact size+CRC32 一致を確認（`work/logs/runtime_parity_sample07_09_all_targets_after_lua_scope_fix_20260305.json`）。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] `10-12` の残failとして `nim: math.sqrt(int)` と `lua: max/min 解決衝突` を修正（Nim emitter に `sqrt` float cast、Lua emitter に `_G.math.max/min`）。`10/11/12` の 14target artifact size+CRC32 一致を確認（`work/logs/runtime_parity_sample10_12_all_targets_after_lua_nim_fix_20260305.json`）。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] `13-15` の `php: stdlib.method.pop` unresolved を修正して fallback 経路を有効化。`13/14/15` の 14target artifact size+CRC32 一致を確認（`work/logs/runtime_parity_sample13_15_all_targets_after_php_pop_fix_20260305.json`）。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] `16-18` の残failを修正（Ruby/Scala/Lua: bit演算記号マップ、Scala: `stdlib.method.*` に `runtime_owner` 注入、Lua: 関数内初回代入の `local` 化 + 宣言-only 追跡）。`16/17/18` の 14target artifact size+CRC32 一致を確認（`work/logs/runtime_parity_sample16_18_all_targets_after_fixes_20260305.json`）。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] 変更影響の回帰確認として `01-03` と `04-06` を全14targetで再実行し、artifact size+CRC32 一致を確認（`work/logs/runtime_parity_sample01_03_all_targets_after_lua_decl_fix_20260305.json`, `work/logs/runtime_parity_sample04_06_all_targets_after_lua_decl_fix_20260305.json`）。これにより sample 18件全てで `pass=18, fail=0` を固定。
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-02`] `docs/ja/how-to-use.md` / `docs/en/how-to-use.md` に parity runbook 節を追加し、全14target実行コマンド、artifact size+CRC32 比較、stale artifact 自動削除、推奨ケース分割を明文化した。
