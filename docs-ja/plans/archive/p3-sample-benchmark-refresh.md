# TASK GROUP: TG-P3-SAMPLE-BENCHMARK

最終更新: 2026-02-23

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P3-SB-01`

最終更新: 2026-02-24

背景:
- サンプルコードの内容変更（例: 07/12 のフレーム数変更）により、既存の実行時間表は最新状態ではなくなっている。
- サンプル番号の再編（04/15/17/18）とサンプル数増加（01〜18）を反映した比較表が必要。

目的:
- 全ターゲット言語の実行時間を再計測し、トップページの比較表を実測値に更新する。

対象:
- `sample/py` の現行サンプル（01〜18）を基準に、Python / C++ / Rust / C# / JS / TS / Go / Java / Swift / Kotlin の実行時間を再計測する。
- `readme.md` と `readme-ja.md` の実行時間表を同一データで更新する。
- サンプル番号・名称・表の行順が `sample/readme.md` / `sample/readme-ja.md` と整合することを確認する。

非対象:
- ベンチマークの最適化作業（コード改善やコンパイルフラグ変更）。
- サンプル内容そのものの追加変更。

受け入れ基準:
- `readme.md` と `readme-ja.md` の実行時間表が、現行サンプル構成（01〜18）と一致している。
- 各言語の計測値が最新再計測結果で更新されている。
- 2つの README で数値不一致がない。

決定ログ:
- 2026-02-23: 低優先タスクとして追加。サンプル変更と番号再編後に、全言語再計測とトップ README 表更新を実施する方針を確定。
- 2026-02-24: `P3-SB-01` を `S1` 〜 `S4` に分解し、まずインポート互換復旧（`P3-SB-01-S1`）を先行実行する。
- 2026-02-24: `P3-SB-01-S1` を完了。`sample/js`/`sample/ts` の `time.js` / runtime 参照を `sample/*/pytra/*` 経由へ揃え、`sample/18` の `class` 初期化欠落と `in` 判定崩れを手修正して、`sample/js/18_mini_language_interpreter` の実行導線を復旧。
- 2026-02-25: `P3-SB-01-S2` 実施。`PYTHONPATH=src python3 sample/py/<file>.py` で `01`〜`18` を再計測。測定値（秒）:
  - 01: 20.7932, 02: 7.6072, 03: 24.4846, 04: 13.6817, 05: 15.4914, 06: 10.3396, 07: 5.5466, 08: 5.7447, 09: 12.6930, 10: 7.0672, 11: 3.8371, 12: 4.3033, 13: 3.8299, 14: 3.0497, 15: 2.9531, 16: 7.8686, 17: 0.3247, 18: 2.5499.
- 2026-02-25: 各実行の stdout を `sample/obj/<no>_py.txt` に保存して再現証跡を保持（`sample/obj` は Git 管理外）。
- 2026-02-25: `P3-SB-01-S3` 実施。`sample/obj/*_js_bench.txt` / `sample/obj/*_ts_bench.txt` を再計測し、`01`〜`18` の JS/TS を収集。C++ は全件でビルド失敗（`src/runtime/cpp/pytra-gen/compiler/east_parts/core.cpp` の `str` 比較/`float64` 曖昧参照および `18_mini_language_interpreter.cpp` の既定引数呼び出しエラー）。Rust/C#/Go/Java/Swift/Kotlin はツールチェイン未導入のため未実施。
- 2026-02-25: `P3-SB-01-S4` 実施方針を確定。JS/TS と Python の最新値を `readme.md` / `readme-ja.md` の比較表に反映し、未測定言語を注記として記録する。

### 分解

- [x] [ID: P3-SB-01-S1] Python/JS/TS のランタイム import 環境を復旧し、`sample/*` の実行時 import 解決を再現可能にする。
- [x] [ID: P3-SB-01-S2] Python 実行を再計測し、`sample/py` 全件の実行時間を収集する。
- [x] [ID: P3-SB-01-S3] C++/Rust/C#/JS/TS/Go/Java/Swift/Kotlin を順次再計測し、環境欠如・既知コンパイル障害を明示記録する。
  - 01〜18 の JS/TS は再計測完了。C++ は全件でビルド失敗（`core.cpp` の文字列比較と `18_mini_language_interpreter` の既定引数不整合）。Rust/C#/Go/Java/Swift/Kotlin はツールチェイン未導入で未実施。
- [x] [ID: P3-SB-01-S4] 計測データを `readme.md` / `readme-ja.md` の比較表に反映し、未計測言語の注記を追加する。
