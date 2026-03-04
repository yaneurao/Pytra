# P0: Java `PyRuntime` から std/utils 実装を除去（SoT正本化）

最終更新: 2026-03-05

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-JAVA-PYRUNTIME-SOT-01`

背景:
- C++ では `src/pytra/std/*.py` / `src/pytra/utils/*.py` を `pytra-gen` へ生成し、`pytra-core` は基盤実装に限定する責務分離が成立している。
- Java では `src/runtime/java/pytra-core/built_in/PyRuntime.java` に `json/pathlib/time/math/png/gif` 由来の実装が残っており、SoT（`src/pytra/*`）から逸脱している。
- この状態では emitter 側が `PyRuntime` 直参照へ退行しやすく、selfhost/runtime 再生成時の整合性が崩れる。

目的:
- Java runtime を C++ と同じ責務境界（`pytra-core` と `pytra-gen`）へ再収束させる。
- `PyRuntime.java` から std/utils 由来実装を撤去し、`src/pytra/*` 正本から生成された `pytra-gen` モジュールへ移管する。
- emitter は EAST3 解決情報を描画するのみとし、ライブラリ固有シンボルを `PyRuntime` へ直書きしない。

対象:
- `src/runtime/java/pytra-core/built_in/PyRuntime.java`
- `src/runtime/java/pytra-gen/std/*.java`（新設）
- `src/runtime/java/pytra-gen/utils/*.java`
- `src/backends/java/emitter/java_native_emitter.py`
- `src/toolchain/compiler/backend_registry.py` / `_static.py`
- `tools/` の SoT ガード・監査

非対象:
- Java 以外 backend の同時改修
- std/utils API 仕様変更
- パフォーマンス最適化

受け入れ基準:
- `PyRuntime.java` に以下の SoT 由来実装が存在しない:
  - JSON: `pyJson*`, `JsonParser`, `jsonStringify/jsonEscapeString`
  - pathlib: `Path` 本体, `pyPath*`
  - time/math: `pyPerfCounter`, `pyMath*`
  - image: `write_rgb_png/save_gif/grayscale_palette`, `pyWriteRGBPNG/pySaveGif/pyGrayscalePalette`
- 上記は `src/pytra/std/*.py` / `src/pytra/utils/*.py` から生成された `src/runtime/java/pytra-gen/{std,utils}/*.java` 側に配置される。
- Java emitter は `resolved_runtime_call` / モジュール解決情報経由で描画し、`PyRuntime` へのライブラリ固有直書き分岐を持たない。
- Java の unit/smoke/sample parity（少なくとも `sample/01,05,18`）が green である。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_emitter_runtimecall_guardrails.py`
- `python3 tools/audit_image_runtime_sot.py --fail-on-core-mix --fail-on-gen-markers`
- `python3 -m unittest discover -s test/unit/backends/java -p 'test_py2java_smoke.py'`
- `python3 tools/runtime_parity_check.py --case-root sample --targets java --samples 01,05,18 --check-artifacts`

実施方針:
1. 先に「境界」と「禁止シンボル」を固定し、退行を CI で止める。
2. `src/pytra/std/*.py` 由来の Java runtime 生成導線を整える（`pytra-gen/std`）。
3. emitter は解決済み IR の描画へ限定し、`PyRuntime` 直参照分岐を縮退。
4. `PyRuntime.java` から SoT 実装を段階削除し、各段で smoke/parity を通してから次へ進む。

## S1 仕様固定（境界 + 棚卸し）

### 1) 責務境界（固定）

| レイヤ | 配置 | 許可内容 | 禁止内容 |
| --- | --- | --- | --- |
| `pytra-core` | `src/runtime/java/pytra-core/built_in/PyRuntime.java` | 汎用プリミティブ（`pyTo*`, `pyBool`, `pyLen`, `pyRange`, `pyAdd/pySub/...`）、コンテナ共通補助、例外/文字列化補助 | `src/pytra/std/*` / `src/pytra/utils/*` 由来のライブラリ実装本体 |
| `pytra-gen/std` | `src/runtime/java/pytra-gen/std/*.java` | `time/json/pathlib/math` の SoT 生成物 | 手書き実装、`PyRuntime` への逆流 |
| `pytra-gen/utils` | `src/runtime/java/pytra-gen/utils/*.java` | `png/gif` など SoT 生成物 | emitter 専用ラッパ名への改名、手書き実装 |
| Java emitter | `src/backends/java/emitter/java_native_emitter.py` | IR で解決済みシンボルの描画 | `PyRuntime.pyJson*` などライブラリ名直書き分岐 |

### 2) `PyRuntime.java` 棚卸し（削除対象と移管先）

| 区分 | 現在 `PyRuntime.java` に存在する主なシンボル | 移管先 | 方針 |
| --- | --- | --- | --- |
| time | `pyPerfCounter` | `pytra-gen/std/time.java` | core から除去し、生成物呼び出しへ統一 |
| math | `pyMathSqrt/Sin/Cos/Tan/Exp/Log/Log10/Fabs/Floor/Ceil/Pow/Pi/E` | `pytra-gen/std/math.java` | core から除去 |
| pathlib | `Path`, `pyPath*` 群 | `pytra-gen/std/pathlib.java` | core から除去 |
| json | `pyJsonDumps/pyJsonLoads`, `jsonStringify/jsonEscapeString`, `JsonParser` | `pytra-gen/std/json.java` | core から除去 |
| image | `write_rgb_png/save_gif/grayscale_palette` と `pyWriteRGBPNG/pySaveGif/pyGrayscalePalette` | `pytra-gen/utils/png.java`, `pytra-gen/utils/gif.java` | `py*` 互換名を含め core から除去 |

## 分解

- [ ] [ID: P0-JAVA-PYRUNTIME-SOT-01-S1-01] Java runtime の責務境界（`pytra-core`/`pytra-gen`）と禁止シンボルを仕様として固定する。
- [ ] [ID: P0-JAVA-PYRUNTIME-SOT-01-S1-02] `PyRuntime.java` 内の SoT 由来実装を棚卸しし、削除対象と移管先（`pytra-gen/std|utils`）を確定する。
- [x] [ID: P0-JAVA-PYRUNTIME-SOT-01-S2-01] `src/pytra/std/{time,json,pathlib,math}.py` の Java 生成導線を整備し、`src/runtime/java/pytra-gen/std/*.java` を生成可能にする。
- [x] [ID: P0-JAVA-PYRUNTIME-SOT-01-S2-02] Java runtime 配布導線（backend registry / runtime hook）を `pytra-core + pytra-gen/std + pytra-gen/utils` 前提へ更新する。
- [ ] [ID: P0-JAVA-PYRUNTIME-SOT-01-S3-01] Java emitter からライブラリ固有 `PyRuntime.*` 直書き分岐を撤去し、解決済み IR 駆動へ移行する。
- [ ] [ID: P0-JAVA-PYRUNTIME-SOT-01-S3-02] Java emitter の回帰テスト（json/pathlib/time/png/gif）を追加し、直書き再混入を防止する。
- [ ] [ID: P0-JAVA-PYRUNTIME-SOT-01-S4-01] `PyRuntime.java` から JSON/pathlib/time/math/image 実装を段階削除し、必要最小限の core API のみに縮退する。
- [ ] [ID: P0-JAVA-PYRUNTIME-SOT-01-S4-02] 静的ガード（`PyRuntime.java` 禁止シンボル検査）を `tools/run_local_ci.py` へ組み込み、再発を fail-fast 化する。
- [x] [ID: P0-JAVA-PYRUNTIME-SOT-01-S4-03] Java smoke/parity（`sample/01,05,18`）を再実施し、artifact 含む一致を確認する。

決定ログ:
- 2026-03-05: ユーザー指示に基づき、`PyRuntime.java` の std/utils 実装残置を P0 として再計画化した。
- 2026-03-05: `perf_counter` だけでなく `json/pathlib/time/math/png/gif` 全体を `PyRuntime.java` から除去対象に含める方針を確定した。
- 2026-03-05: `S1-01` として Java runtime の責務境界を `pytra-core` / `pytra-gen/std` / `pytra-gen/utils` に固定し、禁止事項（core 側 std/utils 実装・emitter 直書き）を明文化した。
- 2026-03-05: `S1-02` として `PyRuntime.java` 内の SoT 由来シンボル棚卸し（time/math/pathlib/json/image）と移管先を確定した。
- 2026-03-05: `S2-01` として `tools/gen_java_std_runtime_from_canonical.py` を追加し、`src/pytra/std/{time,json,pathlib,math}.py` から `src/runtime/java/pytra-gen/std/*.java` を機械生成できる状態を固定した（`--check` 対応）。
- 2026-03-05: `S2-02` として Java runtime hook（host/static backend registry）を `pytra-core + pytra-gen/utils + pytra-gen/std` 配布へ更新した。
- 2026-03-05: `S3-01` の先行段として Java emitter の `write_rgb_png/save_gif/grayscale_palette/json.*` 直書き分岐を撤去し、`runtime_call/resolved_runtime_call` 経由描画へ寄せた（`test_py2java_smoke` green, guardrail green）。
- 2026-03-05: `S3-01` 継続として `resolved_runtime_call` のシンボル素通し化を試行したが、`pytra-gen/std/json.java` の現行生成品質では Java コンパイルが崩れるため、`json.*` は一旦 `PyRuntime.pyJson*` 経路へ戻して継続課題とした。
- 2026-03-05: `S3-02` の先行段として `test_py2java_smoke.py` に emitter 実装ソース検査を追加し、`json/png/gif` の `runtime_call == \"...\"` 直書き分岐再混入を回帰検知化した。
- 2026-03-05: `S4-01` の先行段として `PyRuntime.java` から画像互換ラッパ（`pyWriteRGBPNG/pySaveGif/pyGrayscalePalette`）を削除し、公開名 `write_rgb_png/save_gif/grayscale_palette` のみを残した。
- 2026-03-05: `S4-02` の先行段として `tools/check_java_pyruntime_boundary.py` を追加し、`PyRuntime.java` での画像互換ラッパ再混入を CI fail-fast（`run_local_ci.py` 組み込み）化した。
- 2026-03-05: `S4-03` として `tools/runtime_parity_check.py --case-root sample --targets java --ignore-unstable-stdout` で `01_mandelbrot`, `05_mandelbrot_zoom`, `18_mini_language_interpreter` を再検証し pass（01/05 は artifact size+CRC32 一致）を確認した。
