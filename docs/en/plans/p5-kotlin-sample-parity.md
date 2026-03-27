<a href="../../ja/plans/p5-kotlin-sample-parity.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p5-kotlin-sample-parity.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p5-kotlin-sample-parity.md`

# P5: Kotlin sample parity

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P5-KOTLIN-PARITY-*`

## 背景

pytra-cli の compile → link → emit パイプライン統一後、Kotlin backend の sample parity check を実施したところ 0/18 PASS。

`sample/kotlin/image_runtime.kt` と `py_runtime.kt` の間で `__pytra_write_rgb_png` が重複定義されており、コンパイルエラーになる。重複関数を `image_runtime.kt` から除去済み。

runtime コピー（`py_runtime.kt` + `image_runtime.kt`）を `kotlin.py` に追加し、`pytra-cli.py` に `kotlinc` + `java -jar` の build/run を追加済み。

## 対象

- `src/toolchain/emit/kotlin.py` — runtime コピー
- `sample/kotlin/image_runtime.kt` — 重複関数除去
- `src/pytra-cli.py` — Kotlin build/run

## 非対象

- Kotlin emitter の新規構文サポート追加（既存 sample で使われる範囲のみ）

## 受け入れ基準

- [ ] `runtime_parity_check.py --targets kotlin` で sample/py の全 18 ケースが PASS する。

## 決定ログ

- 2026-03-21: parity check 実施、0/18 PASS で起票。`image_runtime.kt` の `__pytra_write_rgb_png` 重複を除去済み。
- 2026-03-21: VarDecl 対応、`_resolved_runtime_symbol` の dotted call 修正、png/gif module rewrite 追加。7/18 PASS に改善。
- 2026-03-22: `build_import_alias_map` による stdlib 解決を実装。`_native` suffix 命名規約統一。**8/18 PASS**。残り: PNG runtime 互換性(01-04)、型推論不足(10,14,15)、パーサーバグ(18)。
