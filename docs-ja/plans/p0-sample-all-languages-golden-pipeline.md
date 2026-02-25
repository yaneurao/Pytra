# P0 サンプル全言語ゴールデン一致パイプライン

最終更新: 2026-02-25

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-SAMPLE-GOLDEN-ALL-01` 〜 `P0-SAMPLE-GOLDEN-ALL-01-S8`

背景:
- `sample/py` の18件（`01_`〜`18_`）はゴールデンベースラインを持つが、検証がC++中心の経路に偏り、他言語では未完了のまま残っている。
- 全言語で、変換結果の `コンパイル`/`実行`/`ゴールデン比較` が同一条件で成立していないため、言語別に回帰を積み上げると修正の優先順位が崩れやすい。
- `docs-ja/todo` 運用上、変換器変更時の最終受け入れ条件は「未完了P0なし」「全言語全ケースの green」を同時に満たす状態に統一したい。

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
- ターゲット言語ごとの残件は、`docs-ja/plans/p0-sample-all-languages-golden-pipeline.md` に失敗カテゴリ（変換/コンパイル/実行/比較）と再試行条件を残す。

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
   - 結果を `docs-ja/todo/index.md` と `readme-ja.md` / `readme.md` の対応更新（差分が出た場合）へ接続。

子タスク分解（P0-SAMPLE-GOLDEN-ALL-01 の子）:
- `P0-SAMPLE-GOLDEN-ALL-01-S1`: 全件・全言語の検証スコープ確定（サンプル18件、言語9件、比較ルール）
- `P0-SAMPLE-GOLDEN-ALL-01-S2`: runtime parity 実行フローを全言語実行前提（toolchain要件・失敗分類）に整備
- `P0-SAMPLE-GOLDEN-ALL-01-S3`: `cpp` 18件の compile/run/compare 完全一致（ゴールデンベース固定）
- `P0-SAMPLE-GOLDEN-ALL-01-S4`: `rs` 18件の compile/run/compare 完全一致
- `P0-SAMPLE-GOLDEN-ALL-01-S5`: `cs` 18件の compile/run/compare 完全一致
- `P0-SAMPLE-GOLDEN-ALL-01-S6`: `js/ts` 18件の transpile/run/compare 完全一致
- `P0-SAMPLE-GOLDEN-ALL-01-S7`: `go/java/swift/kotlin` 18件の transpile/run/compare 完全一致
- `P0-SAMPLE-GOLDEN-ALL-01-S8`: 全言語集約結果を `readme-ja.md` / `readme.md` のサンプル実行状況とリンクへ反映

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

決定ログ:
- 2026-02-25: 新規P0として追加。全言語/全件一致までを完了条件にする方針を確定。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S1` として検証対象（18サンプル/9言語）と比較ルール（stdout 正規化 + artifact hash/size + source hash）および再現コマンドを固定した。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S2` として runtime parity のケース解決・失敗分類・JSON集計を実装し、`python3 test/unit/test_runtime_parity_check_cli.py` / `python3 test/unit/test_image_runtime_parity.py` / `python3 tools/runtime_parity_check.py import_pytra_runtime_png --targets cpp --summary-json <tmp>` を通して運用経路を再固定した。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S3` として C++ module 解決・runtime tuple unpack・tuple boxing・type_id 初期化順序を修正し、`runtime_parity_check.py --case-root sample --targets cpp --ignore-unstable-stdout` で 18件完走（pass=18）を確認した。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S4` の着手時点で実行環境に `rustc` が存在せず、`runtime_parity_check.py --case-root sample --targets rs --ignore-unstable-stdout` は `toolchain_missing: 18` のみを返した。Rust toolchain 導入後に compile/run 差分修正へ進む。
