# P0 サンプル実行基盤リカバリ

## 背景
`readme-ja.md` の実行速度表は長期的に「欠損値が多い」状態になっており、現在は次の 2 点が重なっています。
- C++ の比較対象コンパイルが失敗し、C++列が未計測
- Rust/C#/Go/Java/Swift/Kotlin の実行環境未導入のため未計測

本タスクでは、まず必要なツールチェインを整備して sample ベンチを全言語で再測定し、`readme-ja.md`（必要なら英語版）を更新する。

## 対応方針
- 0) 全言語実行に必要なチェインをこの環境で導入する（不足がある場合は代替運用・代替条件を明記）。
- 1) C++ の失敗原因をビルド実行で再確認し、失敗が再現しなくなるまで最小修正。
- 2) ベースライン更新可能条件（`tools/verify_sample_outputs.py`）に従ってベンチ計測。
- 3) サンプル実行時間表を `readme-ja.md` と `readme.md` に反映。

## 非対象
- sample 実装そのものの品質改善（出力美化、最適化）は別ID。
- README 文言の最終編集以外、既存リンク構造の変更は本タスク外。

## 受け入れ基準
- 指定した全言語（C++/Rust/C#/JS/TS/Go/Java/Swift/Kotlin）でベンチ測定または実行可否を明示。
- `readme-ja.md` の表に測定結果が反映され、欠損の説明が最新状態を反映している。
- 本タスク完了時に `docs-ja/todo/index.md` の進捗を 1 行更新。

## 決定ログ
- 2026-02-25: `runtime_parity_check` の基盤修正（`core.cpp`/`east_parts/core.py` の比較式分解の堅牢化、`tools/runtime_parity_check.py` の非C++向け `-o` 出力パス合わせ）を反映し、`math_extended` / `pathlib_extended` の `cpp` がPASSを確認。
- 2026-02-25: `src/pytra/std/sys.py` の標準入出力フォールバックを追加し、移植済みランタイムが未定義実装を要求した場合のCI/実行時クラッシュを抑制。
- 2026-02-25: `swiftc` をインストールして実行経路を確立（`tools/runtime_parity_check.py` を `--output` 指定対応＋絶対パス指定 `SWIFTC` 化）。`rust/cs/js/ts/go/java/swift/kotlin` が未修正仕様または生成コード品質の未整合で失敗継続。
- 2026-02-25: Java ターゲットは `public class Main` のファイル名制約により、`runtime_parity_check` で出力先を固定 `Main.java` 化して実行に到達。現状は `Main.main` が TODO スタブ生成のままで出力なしのため検証不合格（実装側 emitter 仕上げが必要）。
- 2026-02-25: `runtime_parity_check --targets cpp,rs,cs,js,ts,go,java,swift,kotlin` を再実行。`math_extended` / `pathlib_extended` は `cpp` のみPASS、`rs` は `crate::pytra` / `crate::math` / `crate::pathlib` の未解決、`cs` は型未解決と `System.IO` 等 import 不足、`js/ts` は `pytra/utils/assertions` import path 404、`go` は `using` 由来の構文誤出力、`java` は出力ミスマッチ（空文字）、`swift` は C#/Kotlin 風 `using` / `public static` を含む未対応言語混入、`kotlin` も同様の構文混入で失敗。
- 2026-02-25: P0-SAMPLE-BENCH-01-S1 完了。`runtime_parity_check` が対象言語全部で skip なく到達することを再確認（`rustc/mcs/mono/go/java/javac/kotlin/node/node` 実行環境 + `swiftc`）。以降は言語別失敗の構文/import 根本不整合に注力。
- 2026-02-25: `P0-SAMPLE-BENCH-02-S1` `tools/runtime_parity_check.py` を `--case-root sample` / `--ignore-unstable-stdout` 対応に拡張し、`sample/py` を `case_root` として参照できるようにした。`python3 tools/runtime_parity_check.py --case-root sample --ignore-unstable-stdout --targets cpp 01_mandelbrot` がPASS。
- 2026-02-25: `tools/verify_sample_outputs.py --refresh-golden --refresh-golden-only` を再実行し、`sample/golden/manifest.json` を 18 件すべて更新（Python実行時基準 + ゴールデンアーティファクト hash/サイズ含む）。
- 2026-02-25: `tools/verify_sample_outputs.py --refresh-golden` 実行時、`OK: 13` `NG: 5` (`06`,`12`,`14`,`16` の artifact hash mismatch、`18` の C++ compile fail)。この時点でベースライン再更新は完了、NG 5件は後続タスクで分解対応が必要。
- 2026-02-25: [P0-SAMPLE-BENCH-02-S1] `01_mandelbrot` を `--targets cpp,rs,cs,js,ts,go,java,swift,kotlin` で再実行。
  - `cpp`: PASS。
  - `rs`: import 解決エラー（`crate::time` / `crate::pytra`）、`bytearray` 未実装、整数と浮動小数点の混在による型エラー多数、`Vec<u8>` への変換不一致。
  - `cs`: `List` 型の `using` 未挿入。
  - `js`, `ts`: `time.js`/`utils/assertions` を解決できず実行不通。
  - `go`: `public` など C# 系構文混入により `package` 宣言以前で parse 失敗。
  - `java`: 出力文字列が空（`Main.main` が未実装か TODO で終了の疑い）。
  - `kotlin`: 同様の C#/Java 構文混入により `public static`、`long`、`System.*` を Kotlin として解釈できず大量コンパイルエラー。
  - `swift`: `swiftc` 未検出で skip。
- 2026-02-25: [P0-SAMPLE-BENCH-02-S2] `02_raytrace_spheres` を `--targets cpp,rs,cs,js,ts,go,java,swift,kotlin` で再実行。
  - `cpp`: PASS。
  - `rs`: `crate::math` / `crate::time` / `crate::pytra` の import 解決エラー、`bytearray` 未実装、`i64` と `f64` の混在型エラー、`i64 -> u8` 変換不足。
  - `cs`: `using math` や `List` の `using` が不足し、名前解決不能。
  - `js`, `ts`: `math.js`/`time.js` 解決エラー（相対 import 出力の解決先不整合）。
  - `go`: `using` / C# 型の混在で `package` 宣言以前に到達せず parse 失敗。
  - `java`: 出力文字列が空（`Main.main` 未到達）。
  - `kotlin`: `using math;`、`public static`、`double`、`List<byte>` など C# 記法混入。
  - `swift`: `swiftc` 未検出で skip。
- 2026-02-25: [P0-SAMPLE-BENCH-02-S2] `03_julia_set` を `--targets cpp,rs,cs,js,ts,go,java,swift,kotlin` で再実行。
  - `cpp`: PASS。
  - `rs`: `crate::time` / `crate::pytra` 未解決、`bytearray` 未実装、`py_break` 未定義、整数と浮動小数点の型不一致、多数の `i64`→`f64` 変換不足。
  - `cs`: `List` import/type 未解決（`System.Collections.Generic` 相当）。
  - `js`, `ts`: `time.js` 相対 import 不在。
  - `go`: `public` など C# 構文混入で parse エラー。
  - `java`: 出力が空（`Main` 系の未実装疑い）。
  - `kotlin`: `public static` / `long` / `List<byte>` 等 C#/Java 記法混入で大量コンパイルエラー。
  - `swift`: toolchain 不在で SKIP。
- 2026-02-25: [P0-SAMPLE-BENCH-02-S2] `04_orbit_trap_julia` を同条件で再実行。
  - `cpp`: PASS。
  - `rs`: `crate::time` / `crate::pytra` 未解決、`bytearray`・`py_break` 未実装、`i64` と `f64` の型演算混在、`u8` 代入時の変換不足、`String` の文字列型不一致。
  - `cs`: `List` import/type 未解決（`System.Collections.Generic` 相当）。
  - `js`, `ts`: `time.js` / `math.js` import 解決失敗。
  - `go`: `public` が混入し `package` 宣言以前で parse エラー。
  - `java`: 出力不一致（期待文字列が空）。
  - `kotlin`: `public static` / `long` / `System.*` / `List<byte>` の言語混在により構文全面で失敗。
  - `swift`: SKIP（toolchain 不在）。
- 2026-02-25: [P0-SAMPLE-BENCH-02-S2] `05_mandelbrot_zoom` を同条件で再実行。
  - `cpp`: PASS。
  - `rs`: `mut`/`_` の未使用、`crate::time` / `crate::pytra.runtime.gif` の未解決、`bytearray`・`bytes` 未実装、`py_break` 未定義、`i64` と `f64` の混在演算、`usize` 混入、型変換不足。
  - `cs`: `List` import/type 未解決。
  - `js`, `ts`: `time.js` import 解決失敗。
  - `go`: `public` 構文混入で parse エラー。
  - `java`: 出力不一致（期待出力が空）。
  - `kotlin`: C#/Java 記法混在（`public static`、`long`、`List<byte>`、`System.Convert`）のため大量コンパイルエラー。
  - `swift`: SKIP（toolchain 不在）。
- 2026-02-25: [P0-SAMPLE-BENCH-02-S2] `06_julia_parameter_sweep` を同条件で再実行。
-  `cpp`: PASS。
-  `rs`: `crate::math` / `crate::time` / `crate::pytra.runtime.gif` の unresolved import、`bytearray`・`bytes` 未実装、`py_break` 未定義、`i64` と `f64` 混在演算、`usize` 混在、`i64+usize` 等のインデックス演算不一致が残存。
-  `cs`: `using math` と `List` の型解決欠如。
-  `js`, `ts`: `math.js` import 解決失敗（`time.js` 系と同様）。
-  `go`: `using`/C# 系記法混入で parse エラー。
-  `java`: 出力不一致（期待文字列が空）。
-  `kotlin`: `using math;` を含む C#/Java 混在構文で大規模なパース/型エラー。
-  `swift`: SKIP（toolchain 不在）。
