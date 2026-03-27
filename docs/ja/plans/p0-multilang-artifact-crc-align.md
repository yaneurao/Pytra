<a href="../../en/plans/p0-multilang-artifact-crc-align.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: sample artifact CRC 一致化（Kotlin gate撤去 + Swift再検証 + fail群修復）

最終更新: 2026-03-04

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01`

背景:
- `tools/runtime_parity_check.py` に artifact CRC32 比較を追加済み（size一致に加えて CRC32 も比較）。
- Kotlin は `ignore_artifacts=True` で artifact 比較を明示スキップしていたため、比較対象として不完全だった。
- `PyPy～Kotlin` / `Swift` の再検証要求に対し、最新実行では多言語で `artifact_missing / artifact_size_mismatch / artifact_crc32_mismatch / run_failed` が発生した。

実測（2026-03-04）:
- Kotlin（gate撤去後）:
  - `python3 tools/runtime_parity_check.py --case-root sample --all-samples --targets kotlin --summary-json work/logs/runtime_parity_sample_kotlin_crc_20260304.json`
  - `cases=18 pass=2 fail=16`
  - `artifact_size_mismatch=4 (01..04)`, `artifact_missing=12 (05..16)`, `ok=2 (17,18)`
- Kotlin（`save_gif` no-op 除去後）:
  - `python3 tools/runtime_parity_check.py --case-root sample --all-samples --targets kotlin --summary-json work/logs/runtime_parity_sample_kotlin_crc_20260304_after_gif.json`
  - `cases=18 pass=6 fail=12`
  - `artifact_missing=0` を確認（`artifact_size_mismatch=4 (01..04)`, `artifact_crc32_mismatch=8 (05,06,08,10,11,12,14,16)`）
- Kotlin（PNG writer を Python stored-block zlib 仕様へ一致化後）:
  - `python3 tools/runtime_parity_check.py --case-root sample --all-samples --targets kotlin --summary-json work/logs/runtime_parity_sample_kotlin_crc_20260304_after_png_store.json`
  - `cases=18 pass=10 fail=8`
  - `artifact_size_mismatch=0` を確認（残件は `artifact_crc32_mismatch=8` のみ）
- PyPy:
  - `work/logs/runtime_parity_sample_pypy_artifact_20260304.json`
  - `ok=16`, `no_artifact_python=2`（artifact生成ケースは size+crc32 一致）
- cpp..kotlin 一括（Swift 未導入時）:
  - `work/logs/runtime_parity_sample_cpp_to_kotlin_crc_20260304.json`
  - 主な失敗:
    - `cpp`: `run_failed`（07,16）+ `artifact_crc32_mismatch`（06,12,14）
    - `cs`: image系で `artifact_crc32_mismatch` 多発
    - `js/ts`: 01..04 が `artifact_size_mismatch`、GIF系で `artifact_crc32_mismatch`
    - `go`: `run_failed` 多発（型 `any` の未確定、palette変換崩れ、sample/18 Token型崩れ）
    - `java`: image系 `artifact_missing` 多発 + `run_failed`
    - `kotlin`: `ok=18` だったが当時は artifact 検証スキップ
- Swift:
  - `swiftly` で `Swift 6.2.4` を導入し `swiftc` を利用可能化。
  - `--targets swift` 再実行で、少なくとも `sample/01..06` は `run_failed`（関数呼び出し引数ラベル不整合）を再現。
- Swift（`--all-samples` 完走ログ固定）:
  - `python3 tools/runtime_parity_check.py --case-root sample --all-samples --targets swift --cmd-timeout-sec 90 --summary-json work/logs/runtime_parity_sample_swift_crc_20260304_all_timeout90.json`
  - `cases=18 pass=0 fail=18`
  - `run_failed=17`, `artifact_missing=1`（`sample/11`）でカテゴリを固定。
- 言語別 baseline lock（Kotlin/Swift 更新反映）:
  - `work/logs/runtime_parity_sample_baseline_lock_20260304.json`
  - `cpp/cs/go/java/js/kotlin/rs/swift/ts` のカテゴリ内訳を固定。
- Java（image call runtime 接続後）:
  - `python3 tools/runtime_parity_check.py --case-root sample --all-samples --targets java --cmd-timeout-sec 120 --summary-json work/logs/runtime_parity_sample_java_crc_20260304_after_image_connect.json`
  - `cases=18 pass=2 fail=16`
  - `artifact_missing=0` を確認（残件: `artifact_size_mismatch=4`, `artifact_crc32_mismatch=7`, `run_failed=5`）
- Java（compile fail 群修正後）:
  - `python3 tools/runtime_parity_check.py --case-root sample --all-samples --targets java --cmd-timeout-sec 120 --summary-json work/logs/runtime_parity_sample_java_crc_20260304_after_compile_fix4.json`
  - `cases=18 pass=6 fail=12`
  - `run_failed=0` を確認（残件: `artifact_size_mismatch=4`, `artifact_crc32_mismatch=8`）
- Go（`__pytra_bytes` + typed演算戻り値修正後）:
  - `python3 tools/runtime_parity_check.py --case-root sample --all-samples --targets go --cmd-timeout-sec 120 --summary-json work/logs/runtime_parity_sample_go_crc_20260304_after_s205b.json`
  - `cases=18 pass=16 fail=2`
  - `run_failed` は `sample/18` のみ（`TokenLike` 残件）へ縮退。`palette must be 256*3 bytes` と `ifexp/min/max` 系 compile fail は解消。
- Go（`TokenLike` フィールドアクセス崩れ修正後）:
  - `python3 tools/runtime_parity_check.py --case-root sample --all-samples --targets go --cmd-timeout-sec 120 --summary-json work/logs/runtime_parity_sample_go_crc_20260304_after_s206.json`
  - `cases=18 pass=17 fail=1`
  - `run_failed=0` を確認（残件は `sample/16` の `artifact_crc32_mismatch=1` のみ）

原因調査（現時点の確定）:
- Kotlin:
  - `src/toolchain/emit/kotlin/emitter/kotlin_native_emitter.py` で `save_gif` が `__pytra_noop` に落ちる。
  - `src/runtime/kotlin/pytra/py_runtime.kt` に GIF writer 実装がない。
  - PNG は `ImageIO` 経路で Python 基準バイナリと不一致（01..04 size mismatch）。
- Java:
  - `src/toolchain/emit/java/emitter/java_native_emitter.py` が `save_gif/write_rgb_png` を `PyRuntime.__pytra_noop` に落としている。
  - runtime 側には `pyWriteRGBPNG/pySaveGif` 実装があるが emitter 接続されていないため artifact 未生成。
  - 追加で `RuntimeError` 参照や `Map.get(key, default)` 互換不足により `run_failed`。
- Go:
  - `__pytra_bytes(v any)` が `[]byte` を扱わず `[]any{}` を返すため、`grayscale_palette()` 経由の palette が空になり GIF で `palette must be 256*3 bytes`。
  - `__pytra_ifexp/__pytra_min/__pytra_max` が `any` を返し、typed代入位置で型アサーション未挿入のため compile fail。
  - sample/18 は `TokenLike` 経由でフィールドアクセスできない型設計崩れ。
- Swift:
  - emitter が関数定義を `f(x:y:...)` 形式で出す一方、呼び出しは `f(a, b, ...)` のままでラベル不一致コンパイルエラー。
- JS/TS:
  - PNG helper が zlib deflate（level=6）を使い、Python runtime とバイナリ形式が一致しない（01..04 size mismatch）。
  - GIF も CRC不一致が多く、writer仕様（LZW/チャンク列/補助値）の差が残る。
- C#:
  - runtime 側に PNG/GIF 実装はあるが imageケースの CRC不一致が継続。writer仕様差か、入力側型変換差の切り分けが必要。
- C++:
  - 07/16 は codegen回帰で compile fail（`object` と typed list の境界、未宣言変数）。
  - 06/12/14 は実行できるが CRC不一致で、画像生成の数値経路差（最適化/型変換/分岐）が疑わしい。

目的:
- Kotlin の artifact スキップを恒久撤去した状態で parity を運用できるようにする。
- Swift toolchain 導入後の Swift parity を正式ログ化し、fail を修復計画へ接続する。
- fail中の backend/runtime を修正し、`sample` の artifact 生成ケースで size+CRC32 一致を達成する。

対象:
- `tools/runtime_parity_check.py`
- `src/toolchain/emit/{kotlin,java,go,swift,js,ts,cs,cpp}/**`
- `src/runtime/{kotlin,java,go,js,ts,cs,cpp}/**`
- `test/unit/test_runtime_parity_check_cli.py`
- `docs/ja/todo/index.md` / 本計画書

非対象:
- 実行時間の最適化
- README ベンチマーク表の更新
- Scala/Ruby/Lua/PHP 側の新規最適化

受け入れ基準:
- `runtime_parity_check --targets kotlin` で artifact 検証が有効なまま実行される。
- `runtime_parity_check --case-root sample --all-samples --targets cpp,rs,cs,js,ts,go,java,swift,kotlin` で
  - `artifact_missing=0`
  - `artifact_size_mismatch=0`
  - `artifact_crc32_mismatch=0`
  - `run_failed=0`
  - `toolchain_missing=0`
- 上記を `summary-json` ログとして保存し、再現手順が文書化される。

確認コマンド（予定）:
- `python3 tools/runtime_parity_check.py --case-root sample --all-samples --targets kotlin --summary-json work/logs/runtime_parity_sample_kotlin_crc_*.json`
- `python3 tools/runtime_parity_check.py --case-root sample --all-samples --targets swift --summary-json work/logs/runtime_parity_sample_swift_crc_*.json`
- `python3 tools/runtime_parity_check.py --case-root sample --all-samples --targets cpp,rs,cs,js,ts,go,java,swift,kotlin --summary-json work/logs/runtime_parity_sample_cpp_to_kotlin_crc_*.json`
- `python3 -m unittest discover -s test/unit -p 'test_runtime_parity_check_cli.py' -v`

決定ログ:
- 2026-03-04: ユーザー指示により、Kotlin artifact スキップ撤去 + Kotlin再検証 + fail群原因調査 + Swift toolchain導入再実行を P0 起票。
- 2026-03-04: Kotlin target の `ignore_artifacts=True` を `tools/runtime_parity_check.py` から撤去。
- 2026-03-04: `Swift 6.2.4` を `swiftly` で導入し、`swiftc` を有効化（`/usr/local/bin/swiftc` symlink）。
- 2026-03-04: Kotlin emitter の `save_gif/grayscale_palette` を runtime helper 接続へ変更し、`src/runtime/kotlin/pytra/py_runtime.kt` に GIF writer（`__pytra_save_gif`）を追加。`artifact_missing` を解消した。
- 2026-03-04: Kotlin `__pytra_write_rgb_png` を Python runtime と同じ stored-block zlib/chunk 構築へ変更し、01..04 の size/CRC mismatch を解消した。
- 2026-03-04: `tools/runtime_parity_check.py` に `--cmd-timeout-sec` を追加し、Swift `sample/09` 長時間化で全体が停止しないようにした。`test_runtime_parity_check_cli.py` 全10件で回帰確認済み。
- 2026-03-04: Swift `--all-samples` を timeout 付きで完走し、`run_failed=17/artifact_missing=1` を baseline としてロックした。
- 2026-03-04: 既存 `cpp..kotlin` ログに Kotlin 更新版と Swift 全件版を合成し、`runtime_parity_sample_baseline_lock_20260304.json` を生成して言語別カテゴリを固定した。
- 2026-03-04: Java emitter の `write_rgb_png/save_gif/grayscale_palette` を `PyRuntime.pyWriteRGBPNG/pySaveGif/pyGrayscalePalette` へ接続し、`artifact_missing` を解消した。
- 2026-03-04: Java compile fail 修正として、`RuntimeError` 呼び出しの文字列化、`dict.get(key, default)` の型付き縮退、`enumerate()` 直接呼び出し、`__pytra_list_repeat` の generic 化、`Dict.entries` emit 対応、`Raise` 終端判定を適用。`run_failed` を 0 にした。
- 2026-03-04: Go runtime に `__pytra_bytes([]byte)` 変換を追加し、GIF palette 空配列化（`palette must be 256*3 bytes`）を解消。Go emitter 側で `ifexp/min/max` 由来式は推論一致時も明示 cast を省略しないよう補強し、typed 代入 compile fail を解消した。
- 2026-03-04: Go `sample/18` 向けに class型付けを「派生を持たない class は `*Class`」へ変更し、`dict.get(default)` runtime helper と `Dict.entries` emit を追加。`TokenLike` フィールドアクセス崩れを解消した。
- 2026-03-04: Swift emitter の `_function_params` を `_ name: Type` 形式へ変更し、定義/呼び出しの引数ラベル不整合（`missing argument labels`）を解消。`sample/01` parity `ok`（`work/logs/runtime_parity_sample_swift_case01_after_s207_20260304.json`）と全sampleコンパイルログで同種エラー消滅（`work/logs/swift_compile_all_after_s207_20260304.log`）を確認。
- 2026-03-04: JS emitter の Call で keyword 引数（`kw_values/kw_nodes`）を位置引数へ合流するよう修正し、`save_gif(delay_cs=..., loop=...)` 欠落を解消。JS/TS PNG helper を Python と同じ stored-block zlib 方式へ置換し、`--targets js,ts --all-samples` 18件で `ok` を確認（`work/logs/runtime_parity_sample_js_ts_crc_20260304_after_s208.json`）。
- 2026-03-04: C# mismatch 原因を切り分け、GIF 側は `save_gif(delay_cs=..., loop=...)` keyword 引数欠落、PNG 側は `py_int` の `Convert.ToInt64` 丸め誤差（Python `int()` と非互換）と確定。C# emitter で keyword 引数合流、`py_runtime.py_int` を `Math.Truncate` 準拠へ修正し、`--targets cs --all-samples` 18件 `ok` を確認（`work/logs/runtime_parity_sample_cs_crc_20260304_after_s209.json`）。
- 2026-03-04: C++ の残件を修正。`if/elif` 事前宣言のスコープ誤り、typed list の `object` 退行、`for y in range(y, h)` の自己初期化崩れ、`math.pi/e` 未初期化、単項 `-` の括弧欠落（`-(a+b)`→`-a+b`）を解消し、`sample/06,07,12,14,16` を再検証して全件 `ok` を確認（`work/logs/runtime_parity_sample_cpp_s210_focus_fixed_20260304.json`）。
- 2026-03-04: Go emitter の二項演算子マッピングに `BitAnd/BitOr/BitXor/LShift/RShift` が欠落し、既定 `+` に崩れる不具合を修正。`sample/16` の `palette_332/quantize_332` が正しいビット演算で生成されることを確認し、`--targets go --all-samples` 18件 `ok` を確認（`work/logs/runtime_parity_sample_go_after_bitop_fix_20260304.json`）。
- 2026-03-04: Kotlin emitter で `keywords`（`save_gif(delay_cs, loop)`）を位置引数へ合流し、`BitAnd/BitOr/BitXor/LShift/RShift` の演算子マッピング欠落を修正。`shl/shr` 右辺を `.toInt()` へ正規化して compile fail を解消し、`--targets kotlin --all-samples` 18件 `ok` を確認（`work/logs/runtime_parity_sample_kotlin_after_shift_int_fix_20260304.json`）。
- 2026-03-04: Java emitter で `keywords` 合流、単項 `-` の括弧崩れ（`-(a+b)`→`-a+b`）修正、`BitAnd/BitOr/BitXor/LShift/RShift` マッピング追加を実施。Java runtime の PNG writer を `Deflater` 依存から Python準拠 stored-block zlib + Adler32 実装へ置換し、`--targets java --all-samples` 18件 `ok` を確認（`work/logs/runtime_parity_sample_java_after_png_unary_fix_20260304.json`）。
- 2026-03-04: `rs,cs,js,ts` を最新コードで再検証し、`--targets rs,cs,js,ts --all-samples` で 18件すべて `ok` を確認（`work/logs/runtime_parity_sample_rs_cs_js_ts_after_s301_20260304.json`）。`S3-01` の残件は Swift 全件完走と `cpp` 全件再実行のみ。
- 2026-03-04: `tools/runtime_parity_check.py` の `run_shell` を `start_new_session=True` + `os.killpg(SIGKILL)` に変更し、timeout 時に子プロセス（`*_swift.out` など）が孤立しないよう修正。合わせて Swift 実行を `swiftc -O` へ変更。
- 2026-03-04: Swift 再検証として `01..04` を実行し、artifact parity が 4/4 `ok` を確認（`work/logs/runtime_parity_sample_swift_01_04_after_s301_progress_20260304.json`）。一方 `--all-samples --cmd-timeout-sec 300` では `05/06/07` が timeout で `run_failed` となることを再確認し、残件を「重いケースの実行戦略（timeout または Swift 側高速化）」へ整理した。
- 2026-03-04: `S3-02` として `test_runtime_parity_check_cli.py` に `swiftc -O` 回帰と timeout 時 process-group kill 回帰を追加。`docs/ja/spec/spec-tools.md` / `docs/en/spec/spec-tools.md` に artifact parity の必須条件（exists+size+CRC32）、stale artifact purge、timeout kill の運用ルールを明記した。
- 2026-03-04: Swift emitter に `Subscript` 代入 fast-path（`Name` への直接添字代入 + `grid[y][x]` write-back）を追加し、`__pytra_setIndex(Any, ...)` の値コピー経路を回避。`05..09` の timeout/CRC失敗が解消し、`--targets swift --all-samples --cmd-timeout-sec 300` は `case_pass=11` まで前進（`work/logs/runtime_parity_sample_swift_all_after_subscript_store_opt_20260304.json`）。
- 2026-03-04: Swift `_call_name` が `Attribute` を解決していなかったため `math.sqrt/sin/...` の型推論が `Any` に落ちる問題を修正。`10/14/15/16` は 4件すべて `ok` を確認（`work/logs/runtime_parity_sample_swift_10_14_15_16_after_callname_attr_20260304.json`）。
- 2026-03-04: Swift `ForCore` を `do { ... }` スコープへ閉じて loop 変数再宣言衝突を解消し、tuple unpack は初回代入時に `var` 宣言するよう修正。`12/13` が `ok` となり、`--targets swift --all-samples --cmd-timeout-sec 300` は `case_pass=17/case_fail=1` まで前進（残件は `18` の compile fail）（`work/logs/runtime_parity_sample_swift_all_after_loop_scope_tuple_decl_20260304.json`）。
- 2026-03-04: Swift `sample/18` の残件として、`main_guard` 直展開による entry 再帰、`main -> __pytra_main` 参照ずれ、`Dict.entries` literal 未対応、dict subscript が runtime helper 経由で値型コピーに落ちる問題を修正。`--targets swift 18_mini_language_interpreter` は `ok` へ復帰（`work/logs/runtime_parity_sample_swift_18_after_dict_fix_20260304.json`）。
- 2026-03-04: `--targets swift --all-samples --cmd-timeout-sec 300` を再実行し、18件すべて `ok` を確認（`work/logs/runtime_parity_sample_swift_all_after_s301_complete_20260304.json`）。`S3-01` の残件は `cpp` 全件再実行のみ。
- 2026-03-04: `--targets cpp --all-samples --cmd-timeout-sec 300` を再実行し、18件すべて `ok` を確認（`work/logs/runtime_parity_sample_cpp_all_after_s301_complete_20260304.json`）。既存の `rs/cs/js/ts/go/java/swift/kotlin` 全件 `ok` ログと合わせて `S3-01` 受け入れ基準（`mismatch/run_failed/toolchain_missing=0`）を充足した。

## 分解

- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S1-01] Kotlin artifact gate 撤去後の baseline（summary-json）を固定し、失敗カテゴリを言語別にロックする。
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S1-02] Swift toolchain 導入後の `--targets swift --all-samples` を完走し、失敗カテゴリをロックする。
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-01] Kotlin: `save_gif` no-op 経路を除去し、runtime GIF writer を実装して 05..16 の artifact_missing を解消する。
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-02] Kotlin: PNG writer を Python準拠バイナリへ寄せ、01..04 の artifact_size/CRC mismatch を解消する。
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-03] Java: emitter の image call を `__pytra_noop` から runtime 実装へ接続し、artifact_missing を解消する。
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-04] Java: `RuntimeError` / dict.get-default / 型周辺の compile fail を修正し、sample 実行を完走可能にする。
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-05] Go: `__pytra_bytes([]byte)` 対応と typed演算戻り値（`ifexp/min/max`）の型確定を修正し、run_failed を解消する。
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-06] Go: sample/18 の `TokenLike` フィールドアクセス崩れを修正し、parser/tokenize 系 compile fail を解消する。
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-07] Swift: 関数定義と呼び出しの引数ラベル整合を修正し、全sampleをコンパイル・実行可能にする。
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-08] JS/TS: PNG/GIF helper を Python準拠バイナリ writer に合わせ、size/CRC mismatch を解消する。
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-09] C#: image系 CRC mismatch の原因（writer仕様差 or 入力変換差）を切り分け、Python準拠バイナリへ合わせる。
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-10] C++: sample/07,16 compile fail を修正し、06/12/14 の CRC mismatch 原因を潰して一致させる。
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S3-01] `cpp,rs,cs,js,ts,go,java,swift,kotlin` 全件で artifact parity を再実行し、`mismatch/run_failed/toolchain_missing=0` を確認する。
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S3-02] 回帰テストと `docs/ja/spec` に artifact parity 運用（CRC32必須）を反映する。
