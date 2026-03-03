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

原因調査（現時点の確定）:
- Kotlin:
  - `src/backends/kotlin/emitter/kotlin_native_emitter.py` で `save_gif` が `__pytra_noop` に落ちる。
  - `src/runtime/kotlin/pytra/py_runtime.kt` に GIF writer 実装がない。
  - PNG は `ImageIO` 経路で Python 基準バイナリと不一致（01..04 size mismatch）。
- Java:
  - `src/backends/java/emitter/java_native_emitter.py` が `save_gif/write_rgb_png` を `PyRuntime.__pytra_noop` に落としている。
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
- `src/backends/{kotlin,java,go,swift,js,ts,cs,cpp}/**`
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

## 分解

- [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S1-01] Kotlin artifact gate 撤去後の baseline（summary-json）を固定し、失敗カテゴリを言語別にロックする。
- [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S1-02] Swift toolchain 導入後の `--targets swift --all-samples` を完走し、失敗カテゴリをロックする。
- [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-01] Kotlin: `save_gif` no-op 経路を除去し、runtime GIF writer を実装して 05..16 の artifact_missing を解消する。
- [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-02] Kotlin: PNG writer を Python準拠バイナリへ寄せ、01..04 の artifact_size/CRC mismatch を解消する。
- [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-03] Java: emitter の image call を `__pytra_noop` から runtime 実装へ接続し、artifact_missing を解消する。
- [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-04] Java: `RuntimeError` / dict.get-default / 型周辺の compile fail を修正し、sample 実行を完走可能にする。
- [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-05] Go: `__pytra_bytes([]byte)` 対応と typed演算戻り値（`ifexp/min/max`）の型確定を修正し、run_failed を解消する。
- [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-06] Go: sample/18 の `TokenLike` フィールドアクセス崩れを修正し、parser/tokenize 系 compile fail を解消する。
- [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-07] Swift: 関数定義と呼び出しの引数ラベル整合を修正し、全sampleをコンパイル・実行可能にする。
- [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-08] JS/TS: PNG/GIF helper を Python準拠バイナリ writer に合わせ、size/CRC mismatch を解消する。
- [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-09] C#: image系 CRC mismatch の原因（writer仕様差 or 入力変換差）を切り分け、Python準拠バイナリへ合わせる。
- [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-10] C++: sample/07,16 compile fail を修正し、06/12/14 の CRC mismatch 原因を潰して一致させる。
- [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S3-01] `cpp,rs,cs,js,ts,go,java,swift,kotlin` 全件で artifact parity を再実行し、`mismatch/run_failed/toolchain_missing=0` を確認する。
- [ ] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S3-02] 回帰テストと `docs/ja/spec` に artifact parity 運用（CRC32必須）を反映する。
