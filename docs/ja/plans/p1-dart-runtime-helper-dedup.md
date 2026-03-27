<a href="../../en/plans/p1-dart-runtime-helper-dedup.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: Dart emitter ランタイムヘルパー重複排除

## 背景

Dart emitter は各生成ファイル（`01_mandelbrot.dart`, `std/time.dart`, `utils/png.dart` 等）にランタイムヘルパー関数をインラインで埋め込んでいる。同一プログラム内の複数ファイルで同一関数が重複定義され、コード膨張と保守コストが発生している。

## 対象ヘルパー

各生成ファイルに埋め込まれている以下の関数群（`// --- pytra runtime helpers ---` ブロック）:

- `__pytraPrintRepr()` — Python 風 repr 変換
- `__pytraPrint()` — print 関数
- `__pytraTruthy()` — Python truthiness 判定
- `__pytraContains()` — `in` 演算子
- `__pytraRepeatSeq()` — `*` 演算子（文字列/リスト繰り返し）
- `__pytraStrIsdigit()` / `__pytraStrIsalpha()` / `__pytraStrIsalnum()` — 文字列述語
- `__pytraIsinstance()` — isinstance ヘルパー

## 方針

1. 上記関数を `src/runtime/dart/built_in/py_runtime.dart` に集約する。
2. emitter の `_emit_print_helper()` / `_emit_truthy_helper()` 等のインライン生成メソッドを除去する。
3. 各生成ファイルは `import '{root_rel_prefix}built_in/py_runtime.dart';` 経由でヘルパーにアクセスする（既に import 済み）。

## 非対象

- `pytraInt()` / `pytraFloat()` / `pytraSlice()` / `pytraStrSlice()` 等は既に `py_runtime.dart` に存在しており変更不要。
- `py_runtime.dart` の関数名は `__pytra` prefix を維持する（Dart には export 制御がないが、ユーザーコードとの衝突回避のため）。

## 受け入れ基準

1. 生成ファイルから `// --- pytra runtime helpers ---` ブロックが消える。
2. `py_runtime.dart` に全ヘルパーが集約される。
3. sample/py 全 18 ケースが Dart でバイナリ一致する。

## 決定ログ

- 2026-03-23: 計画書作成。
