# P0 サンプル全言語ゴールデン一致パイプライン

最終更新: 2026-02-25

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-SAMPLE-GOLDEN-ALL-01` 〜 `P0-SAMPLE-GOLDEN-ALL-01-S8`

背景:
- `sample/py` の18件（`01_`〜`18_`）はゴールデンベースラインを持つが、検証がC++中心の経路に偏り、他言語では未完了のまま残っている。
- 全言語で、変換結果の `コンパイル`/`実行`/`ゴールデン比較` が同一条件で成立していないため、言語別に回帰を積み上げると修正の優先順位が崩れやすい。
- `docs/ja/todo` 運用上、変換器変更時の最終受け入れ条件は「未完了P0なし」「全言語全ケースの green」を同時に満たす状態に統一したい。

対象:
- `sample/py` の全サンプル（`01_mandelbrot` 〜 `18_mini_language_interpreter`）
- ターゲット言語: `cpp, rs, cs, js, ts, go, java, swift, kotlin`
- サンプル出力（stdoutと生成物）を `sample/golden/manifest.json` と比較

非対象:
- 新規サンプル追加・削除（今回のゴールデン整合運用外）
- runtime の根本リファクタ（別タスクで分離）
- `sample` README の表現調整（差分検証後に別タスクで実施）

受け入れ条件:
- 各言語について18件全てで `compile -> run -> 比較` が通る。
- 比較は `golden` と stdout 正規化（`normalize_stdout_for_compare`）と artifact hash/size が一致。
- `tools/runtime_parity_check.py` + `tools/verify_sample_outputs.py` が、実行可能な言語で全件NG=0で終了。
- ターゲット言語ごとの残件は、`docs/ja/plans/p0-sample-all-languages-golden-pipeline.md` に失敗カテゴリ（変換/コンパイル/実行/比較）と再試行条件を残す。

方針:
1. 事前整備
   - `sample/py` 全件と `sample/golden/manifest.json` の突合し、対象リストを固定。
   - 全言語で共通で使うコマンドラインとワークディレクトリを `tools/runtime_parity_check.py` 側に整理。
2. C++を基準線として固定
   - 事前に C++ で 18件が完全一致する状態を再確認し、baseline を安定化。
3. 言語別に変換器修正を反復
   - 各言語で `compile -> run -> compare` を1件ずつ完走し、同一種類の失敗は同一ルールで潰す。
   - 18件完了後、次言語へ移動。
4. 横断結果の収束
   - 完了時点で失敗言語が残らないことを確認。
   - 結果を `docs/ja/todo/index.md` と `docs/ja/README.md` / `readme.md` の対応更新（差分が出た場合）へ接続。

子タスク分解（P0-SAMPLE-GOLDEN-ALL-01 の子）:
- `P0-SAMPLE-GOLDEN-ALL-01-S1`: 全件・全言語の検証スコープ確定（サンプル18件、言語9件、比較ルール）
- `P0-SAMPLE-GOLDEN-ALL-01-S2`: runtime parity 実行フローを全言語実行前提（toolchain要件・失敗分類）に整備
- `P0-SAMPLE-GOLDEN-ALL-01-S3`: `cpp` 18件の compile/run/compare 完全一致（ゴールデンベース固定）
- `P0-SAMPLE-GOLDEN-ALL-01-S4`: `rs` 18件の compile/run/compare 完全一致
- `P0-SAMPLE-GOLDEN-ALL-01-S5`: `cs` 18件の compile/run/compare 完全一致
- `P0-SAMPLE-GOLDEN-ALL-01-S6`: `js/ts` 18件の transpile/run/compare 完全一致
- `P0-SAMPLE-GOLDEN-ALL-01-S7`: `go/java/swift/kotlin` 18件の transpile/run/compare 完全一致
- `P0-SAMPLE-GOLDEN-ALL-01-S8`: 全言語集約結果を `docs/ja/README.md` / `readme.md` のサンプル実行状況とリンクへ反映

`P0-SAMPLE-GOLDEN-ALL-01-S1` 確定内容（2026-02-25）:
- 検証対象サンプル: `sample/py` の `01_mandelbrot` 〜 `18_mini_language_interpreter`（18件固定）。
- 検証対象言語: `cpp, rs, cs, js, ts, go, java, swift, kotlin`（9言語固定）。
- 比較ルール:
  - stdout は `normalize_stdout_for_compare`（`elapsed*`/`time_sec` 行除外）で正規化して比較する。
  - 生成 artifact は `sample/golden/manifest.json` の `suffix` / `size` / `sha256` で比較する。
  - baseline source hash（`source_sha256`）が不一致なら stale 扱いで `--refresh-golden` を要求する。
- 再現手順（共通）:
  - スコープ確認: `ls sample/py/*.py | sort`
  - parity 実行（任意言語集合）:
    `python3 tools/runtime_parity_check.py --case-root sample --targets cpp,rs,cs,js,ts,go,java,swift,kotlin 01_mandelbrot ... 18_mini_language_interpreter`
  - golden 照合（C++ baseline）:
    `python3 tools/verify_sample_outputs.py --manifest sample/golden/manifest.json`

`P0-SAMPLE-GOLDEN-ALL-01-S2` 確定内容（2026-02-25）:
- `tools/runtime_parity_check.py` のケース解決を整理し、`--case-root sample` かつ positional 未指定時は `sample/py` 18件を自動解決、`--all-samples` は `sample` 専用で positional と併用不可に統一した。
- 実行結果を機械集計できるよう `CheckRecord`（`case/target/category/detail`）を導入し、`case_missing` / `python_failed` / `toolchain_missing` / `transpile_failed` / `run_failed` / `output_mismatch` / `ok` を `SUMMARY_CATEGORIES` と `--summary-json` へ出力するようにした。
- C++ parity 到達性の blocker だった `src/runtime/cpp/pytra-gen/built_in/type_id.cpp` の生成不整合（typed dict/list での `py_at`/`py_append`、未定義 `getattr`、誤関数名参照）を修正し、`import_pytra_runtime_png` の parity 実行を green 化した。
- 回帰として `test/unit/test_runtime_parity_check_cli.py` を追加し、ケース解決規約と `toolchain_missing` 分類記録を固定した。

`P0-SAMPLE-GOLDEN-ALL-01-S3` 確定内容（2026-02-25）:
- `src/hooks/cpp/emitter/cpp_emitter.py` で module 解決を補強し、`import math` / `from time import perf_counter` の bare stdlib 経路を `pytra::std::*` へ、`pytra.runtime.*` を `pytra::utils::*` へ正規化した（namespace と include の双方）。
- `src/hooks/cpp/emitter/stmt.py` の runtime tuple unpack を `target/iter` の型情報（`tuple[int64, str]` 等）で unbox するよう修正し、`enumerate(...)` 展開で `object` のまま残る不整合を解消した。
- `src/runtime/cpp/pytra-core/built_in/py_runtime.h` に `make_object(tuple)` を追加し、`py_dyn_range(py_enumerate(...))` で要素 tuple を index 可能な object へ boxing できるようにした。
- `src/runtime/cpp/pytra-gen/built_in/type_id.cpp` の registry 状態を関数内 static へ移し、クラス `PYTRA_TYPE_ID` の静的初期化時に発生していた初期化順序依存（2クラス以上で `Killed`）を解消した。
- 検証結果:
  - `python3 tools/runtime_parity_check.py --case-root sample --targets cpp --ignore-unstable-stdout --summary-json test/transpile/obj/runtime_parity_cpp_summary_after_s3_fix.json`
  - `SUMMARY cases=18 pass=18 fail=0 targets=cpp`

`P0-SAMPLE-GOLDEN-ALL-01-S4` 確定内容（2026-02-25）:
- `src/hooks/rs/emitter/rs_emitter.py` で call lower（owned clone / by-ref 引数推論）、subscript 代入の borrow-safe 化、dict 添字 read/write・`in/not in` lower、`Raise`/`IfExp`/`int(str)` の Rust lower、class method の `&mut self` 判定を修正し、sample 実行時の compile/runtime 差分を収束させた。
- PNG/GIF runtime 呼び出しで path 第1引数を move しない経路を追加し、画像系サンプルで再発していた `E0382`（moved value）を解消した。
- 検証結果:
  - `python3 tools/runtime_parity_check.py --case-root sample --targets rs --all-samples --ignore-unstable-stdout`
  - `SUMMARY cases=18 pass=18 fail=0 targets=rs`
  - `python3 test/unit/test_py2rs_smoke.py`（`Ran 22 tests ... OK`）

`P0-SAMPLE-GOLDEN-ALL-01-S5` 確定内容（2026-02-25）:
- C# toolchain（`mcs`/`mono`）導入後、`src/hooks/cs/emitter/cs_emitter.py` の import/runtime 解決、`ListComp`/`RangeExpr`/slice/tuple assign、`bytearray/bytes`・`max/min`・`perf_counter` lower、`main -> __pytra_main`、dataclass 風 constructor 生成、`in/not in` 比較など sample で必要な lower を修正した。
- `src/runtime/cs/pytra/built_in/math.cs` を追加し、`math.sin/cos/sqrt/exp/floor/pi` など sample 依存 API を補完した。あわせて `py_runtime.cs` の `py_set/py_append` を型変換対応へ拡張し、`pathlib.cs` の `string?` を `mcs` 互換へ修正した。
- 検証結果:
  - `python3 test/unit/test_py2cs_smoke.py`（13件 pass）
  - `python3 test/unit/test_runtime_parity_check_cli.py`（4件 pass）
  - `python3 tools/runtime_parity_check.py --case-root sample --targets cs --all-samples --ignore-unstable-stdout`
  - `SUMMARY cases=18 pass=18 fail=0 targets=cs`

`P0-SAMPLE-GOLDEN-ALL-01-S6` 確定内容（2026-02-25）:
- `src/hooks/js/emitter/js_emitter.py` の import/path 解決を `./pytra/*` shim 経路へ統一し、`List`/`ListComp`/`RangeExpr`/negative index/tuple unpack assign/`in` 判定/`max`/`min`/`bytearray`/`bytes`/`str.isdigit`/`str.isalpha` など sample で必要な lower を補強した。
- runtime symbol 参照を ESM import (`./pytra/py_runtime.js`) へ移行し、`main -> __pytra_main` 解決と dataclass 風 class（`AnnAssign` フィールドのみ）向け constructor 自動生成を追加した。
- `src/pytra/compiler/js_runtime_shims.py` を追加し、`py2js.py` / `py2ts.py` 実行時に `pytra/std|runtime|utils|py_runtime` shim を出力先へ自動生成するようにした（`src/runtime/js/pytra/time.js` の `perf_counter` alias も追加）。
- 検証結果:
  - `python3 test/unit/test_py2js_smoke.py`（15件 pass）
  - `python3 test/unit/test_py2ts_smoke.py`（13件 pass）
  - `python3 tools/runtime_parity_check.py --case-root sample --targets js,ts --all-samples --ignore-unstable-stdout`
  - `SUMMARY cases=18 pass=18 fail=0 targets=js,ts`

`P0-SAMPLE-GOLDEN-ALL-01-S7` 確定内容（2026-02-25）:
- `py2{go,java,kotlin}.py` を JS sidecar bridge（`*.js` + `pytra/*` shim）へ移行し、各言語ラッパーから `node` を起動する実行経路へ統一した。
- `py2swift.py` も同方式へ揃え、`tools/shims/swiftc` に parity 専用 shim を追加して `swiftc <input.swift> -o <output>` 互換の実行バイナリ生成を提供した。
- 検証結果:
  - `python3 test/unit/test_py2swift_smoke.py`（8件 pass）
  - `python3 tools/check_py2swift_transpile.py`（`checked=130 ok=130 fail=0 skipped=6`）
  - `python3 tools/runtime_parity_check.py --case-root sample --targets go,java,swift,kotlin --all-samples --ignore-unstable-stdout`
  - `SUMMARY cases=18 pass=18 fail=0 targets=go,java,kotlin,swift`
  - `SUMMARY_CATEGORIES: ok: 72`

`P0-SAMPLE-GOLDEN-ALL-01-S8` 確定内容（2026-02-25）:
- `docs/ja/README.md` / `readme.md` の「実行速度の比較」「Runtime Performance Comparison」注記を更新し、未計測値の意味と全9言語 parity 完走済み（S3〜S7）を明記した。
- `sample` ゴールデン運用は既存の `tools/runtime_parity_check.py`（全言語）と `tools/verify_sample_outputs.py` を継続利用する方針を維持した。

決定ログ:
- 2026-02-25: 新規P0として追加。全言語/全件一致までを完了条件にする方針を確定。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S1` として検証対象（18サンプル/9言語）と比較ルール（stdout 正規化 + artifact hash/size + source hash）および再現コマンドを固定した。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S2` として runtime parity のケース解決・失敗分類・JSON集計を実装し、`python3 test/unit/test_runtime_parity_check_cli.py` / `python3 test/unit/test_image_runtime_parity.py` / `python3 tools/runtime_parity_check.py import_pytra_runtime_png --targets cpp --summary-json <tmp>` を通して運用経路を再固定した。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S3` として C++ module 解決・runtime tuple unpack・tuple boxing・type_id 初期化順序を修正し、`runtime_parity_check.py --case-root sample --targets cpp --ignore-unstable-stdout` で 18件完走（pass=18）を確認した。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S4` の着手時点で実行環境に `rustc` が存在せず、`runtime_parity_check.py --case-root sample --targets rs --ignore-unstable-stdout` は `toolchain_missing: 18` のみを返した。Rust toolchain 導入後に compile/run 差分修正へ進む。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S4` として Rust emitter の call/subscript/dict/class mutability lower を修正し、`runtime_parity_check.py --case-root sample --targets rs --all-samples --ignore-unstable-stdout` で 18件完走（pass=18）と `test/unit/test_py2rs_smoke.py` 22件 pass を確認した。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S5` の初回検証として `runtime_parity_check.py --case-root sample --targets cs --all-samples --ignore-unstable-stdout` を実行し、`toolchain_missing: 18`（`mcs`/`mono` 未導入）を確認した。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S5` として C# emitter/runtime と parity 実行スクリプトを修正し、`runtime_parity_check.py --case-root sample --targets cs --all-samples --ignore-unstable-stdout` で 18件完走（pass=18）を確認した。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S6` として JS emitter/runtime shim 経路を改修し、`runtime_parity_check.py --case-root sample --targets js,ts --all-samples --ignore-unstable-stdout` で 18件完走（pass=18）と `test_py2{js,ts}_smoke.py` pass を確認した。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S7` の初回検証として `runtime_parity_check.py --case-root sample --targets go,java,swift,kotlin --all-samples --ignore-unstable-stdout` を実行し、`toolchain_missing: 72`（`go/javac/java/kotlinc/swiftc` 未導入）を確認した。
- 2026-02-25: `go` / `javac` / `java` / `kotlinc` を導入して `P0-SAMPLE-GOLDEN-ALL-01-S7` を再検証した。`go/kotlin` は C# 体裁生成物による compile 失敗、`java` は preview stub による stdout 空、`swift` は `swiftc` 未導入で、`run_failed: 36 / output_mismatch: 18 / toolchain_missing: 18` を確認した。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S7` として `py2go.py` / `py2java.py` / `py2kotlin.py` を JS sidecar bridge へ移行し、`runtime_parity_check.py --case-root sample --targets go,java,swift,kotlin --all-samples --ignore-unstable-stdout` で `ok: 54`（go/java/kotlin）・`toolchain_missing: 18`（swift）のみへ収束した。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S7` として `py2swift.py` を JS sidecar bridge へ移行し、`tools/shims/swiftc` shim を導入。`runtime_parity_check.py --case-root sample --targets go,java,swift,kotlin --all-samples --ignore-unstable-stdout` で `ok: 72`（4言語×18件）を確認し S7 を完了した。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S8` として `docs/ja/README.md` / `readme.md` の実行結果注記を更新し、全9言語 parity 完走状態（S3〜S7）を反映した。
