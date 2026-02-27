# P4: 全言語 selfhost 完全化（低低優先）

最終更新: 2026-02-27

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P4-MULTILANG-SH-01`

背景:
- 現状の multilang selfhost 状態では、C++ 以外に `stage1/stage2/stage3` の未達が残っている。
- `rs` は stage1 失敗、`cs`/`js` は stage2 失敗、`ts` は preview-only、`go/java/swift/kotlin` は multistage runner 未定義。
- 将来的に「全言語で自己変換チェーンが成立する」状態を作るため、低低優先で長期バックログ化する。

目的:
- `py2<lang>.py`（`cpp/rs/cs/js/ts/go/java/swift/kotlin`）の selfhost 成立条件を段階的に満たし、全言語で multistage 監視を通せる状態へ収束する。

対象:
- `tools/check_multilang_selfhost_stage1.py` / `tools/check_multilang_selfhost_multistage.py` / `tools/check_multilang_selfhost_suite.py`
- 各言語の `py2*.py` と対応 emitter/runtime
- selfhost 検証レポート（`docs-ja/plans/p1-multilang-selfhost-*.md`）の更新導線

非対象:
- 速度最適化やコードサイズ最適化
- backend 全面再設計（selfhost 成立に不要な大規模改修）
- 優先度 `P0` / `P1` / `P3` の既存タスクを追い越す着手

受け入れ基準:
- `tools/check_multilang_selfhost_suite.py` 実行結果で全言語が `stage1 pass` となる。
- multistage レポートで全言語が `stage2 pass` / `stage3 pass`（または明示的な恒久除外）になる。
- `runner_not_defined` / `preview_only` / `toolchain_missing` 依存の常態化が解消される。

確認コマンド:
- `python3 tools/check_multilang_selfhost_suite.py`
- `python3 tools/check_multilang_selfhost_stage1.py`
- `python3 tools/check_multilang_selfhost_multistage.py`
- `python3 tools/build_selfhost.py`

決定ログ:
- 2026-02-27: ユーザー要望により、全言語 selfhost 完全化を低低優先（P4）で TODO 追加する方針を確定した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S1-01`] `python3 tools/check_multilang_selfhost_suite.py` を再実行し、`docs-ja/plans/p1-multilang-selfhost-status.md` / `docs-ja/plans/p1-multilang-selfhost-multistage-status.md` を更新した。未達カテゴリを言語別に固定し、blocking chain を確定した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S1-02`] `runner_not_defined` 対象（go/java/swift/kotlin）の multistage runner 契約を定義し、`check_multilang_selfhost_multistage.py` へ段階実装する API 形を確定した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-01`] `src/py2rs.py` の括弧付き `from-import` を selfhost parser 互換の単一行 import へ修正し、`python3 tools/check_multilang_selfhost_stage1.py` / `python3 tools/check_multilang_selfhost_multistage.py` で `rs stage1=pass` を確認した。`rs` の先頭失敗は `stage1_transpile_fail` から `compile_fail`（stage2 build）へ遷移した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S1`] C# emitter の selfhost compile 阻害を一段解消（`Path` alias/constructor, `str.endswith|startswith` 変換, 関数定義の定数デフォルト引数出力）。`check_multilang_selfhost_*` 再実行で `cs` の先頭失敗が `Path` 未解決から `sys` 未解決へ遷移し、次ブロッカーを特定した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S1`] C# emitter で `sys.exit` を `System.Environment.Exit` へ lower し、文字列 docstring 式の不要出力を抑止した。`check_multilang_selfhost_*` 再実行で `cs` の先頭失敗が `sys` 未解決から `transpile_to_csharp` 未解決へ遷移し、import 依存閉包（単体 selfhost source 生成 or モジュール連結）の実装が次ブロッカーと確定した。
- 2026-02-27: [ID: `P4-MULTILANG-SH-01-S2-02-S2-S2-S1`] 単体 selfhost source 方式の PoC として `tools/prepare_selfhost_source_cs.py` を追加し `selfhost/py2cs.py` を生成。`python3 src/py2cs.py selfhost/py2cs.py -o /tmp/cs_selfhost_full_stage1.cs` を検証した結果、`unsupported_syntax: object receiver attribute/method access is forbidden by language constraints`（`selfhost/py2cs.py` 変換中）で停止し、現行 C# 制約下では PoC が未通過であることを確認した。

## 現状固定（S1-01）

言語別未達要因（2026-02-27）:

| lang | stage1 | stage2 | stage3 | category | 先頭原因 |
| --- | --- | --- | --- | --- | --- |
| rs | fail | skip | skip | `stage1_transpile_fail` | `unsupported from-import clause` |
| cs | pass | fail | skip | `compile_fail` | `Path` 型未解決（`System.IO` 参照不足） |
| js | pass | fail | skip | `stage1_dependency_transpile_fail` | JS emitter の `object receiver attribute/method access` 制約違反 |
| ts | pass | blocked | blocked | `preview_only` | 生成 transpiler が preview-only |
| go | pass | skip | skip | `runner_not_defined` | multistage runner 未定義 |
| java | pass | skip | skip | `runner_not_defined` | multistage runner 未定義 |
| swift | pass | skip | skip | `runner_not_defined` | multistage runner 未定義 |
| kotlin | pass | skip | skip | `runner_not_defined` | multistage runner 未定義 |

優先順（blocking chain）:
1. `rs` の stage1 失敗を解消（以降の stage2/stage3 検証が不可）。
2. `cs` の stage2 compile 失敗を解消（stage3 へ進めない）。
3. `js` の stage2 依存 transpile 失敗を解消（stage3 へ進めない）。
4. `ts` の preview-only を解消（stage2/stage3 の評価自体が blocked）。
5. `go/java/swift/kotlin` の runner 契約を定義し、`runner_not_defined` を解消して multistage 監視対象へ昇格。

## Runner 契約（S1-02）

目的:
- `check_multilang_selfhost_multistage.py` の `runner_not_defined` を、言語別 adapter 実装で段階的に置換する。

共通 API 契約（実装方針）:
1. `build_stage1(lang, stage1_src, stage1_runner)`:
   - stage1 生成 transpiler ソース（`stage1_src`）を実行可能 runner（binary/jar）へ変換する。
2. `run_stage2(lang, stage1_runner, src_py, stage2_src)`:
   - stage1 runner で `src/py2<lang>.py` を再変換し、`stage2_src` を生成する。
3. `build_stage2(lang, stage2_src, stage2_runner)`:
   - stage2 transpiler ソースを実行可能 runner へ変換する。
4. `run_stage3(lang, stage2_runner, sample_py, stage3_out)`:
   - stage2 runner で `sample/py/01_mandelbrot.py` を変換し、`stage3_out` 生成有無で pass/fail 判定する。

言語別 runner 契約:

| lang | build_stage1 / build_stage2 | run_stage2 / run_stage3 | 成功条件 |
| --- | --- | --- | --- |
| go | `go build -o <runner> <stage*.go>` | `<runner> <input.py> -o <out.go>` | `out.go` が生成される |
| java | `javac <stage*.java>`（main class は stage 出力規約で固定） | `java -cp <dir> <main_class> <input.py> -o <out.java>` | `out.java` が生成される |
| swift | `swiftc <stage*.swift> -o <runner>` | `<runner> <input.py> -o <out.swift>` | `out.swift` が生成される |
| kotlin | `kotlinc <stage*.kt> -include-runtime -d <runner.jar>` | `java -jar <runner.jar> <input.py> -o <out.kt>` | `out.kt` が生成される |

実装時の fail 分類ルール:
- build 失敗: `compile_fail` / `stage2_compile_fail`
- 実行失敗: `self_retranspile_fail` / `sample_transpile_fail`
- 生成物欠落: 実行失敗カテゴリへ含め、`output missing` を note に付与

## 分解

- [x] [ID: P4-MULTILANG-SH-01-S1-01] 現状の stage1/stage2/stage3 未達要因を言語別に固定化し、優先順（blocking chain）を明文化する。
- [x] [ID: P4-MULTILANG-SH-01-S1-02] multistage runner 未定義言語（go/java/swift/kotlin）の runner 契約を定義し、`runner_not_defined` を解消する実装方針を確定する。
- [x] [ID: P4-MULTILANG-SH-01-S2-01] Rust selfhost の stage1 失敗（from-import 受理）を解消し、stage2 へ進める。
- [ ] [ID: P4-MULTILANG-SH-01-S2-02] C# selfhost の stage2 compile 失敗を解消し、stage3 変換を通す。
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S1] C# emitter の selfhost 互換ギャップ（`Path`/`str.endswith|startswith`/定数デフォルト引数）を埋め、先頭 compile エラーを前進させる。
- [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2] `py2cs.py` selfhost 生成物の import 依存解決方針（単体 selfhost source 生成 or モジュール連結）を確定し、`sys/argparse/transpile_cli` 未解決を解消する。
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S1] C# selfhost 先頭エラーの足切り（`sys.exit` / docstring式）を解消し、import 依存未解決の先頭シンボルを確定する。
- [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2] C# selfhost 用の import 依存閉包方式（単体 selfhost source 生成 or モジュール連結）を実装し、`transpile_to_csharp` 未解決を解消する。
- [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S1] 単体 selfhost source 方式の PoC（`prepare_selfhost_source_cs.py`）を実装し、変換可否を実測で確認する。
- [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2] PoC 失敗要因（C# object receiver 制約）を解消するか、モジュール連結方式へ pivot して import 依存閉包を成立させる。
- [ ] [ID: P4-MULTILANG-SH-01-S2-02-S3] C# selfhost の stage2/stage3 を通し、`compile_fail` から `pass` へ到達させる。
- [ ] [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost の stage2 依存 transpile 失敗を解消し、multistage を通す。
- [ ] [ID: P4-MULTILANG-SH-01-S3-01] TypeScript の preview-only 状態を解消し、selfhost 実行可能な生成モードへ移行する。
- [ ] [ID: P4-MULTILANG-SH-01-S3-02] Go/Java/Swift/Kotlin の native backend 化タスクと接続し、selfhost 実行チェーンを有効化する。
- [ ] [ID: P4-MULTILANG-SH-01-S4-01] 全言語 multistage 回帰を CI 導線へ統合し、失敗カテゴリの再発を常時検知できるようにする。
- [ ] [ID: P4-MULTILANG-SH-01-S4-02] 完了判定テンプレート（各言語の stage 通過条件と除外条件）を文書化し、運用ルールを固定する。
