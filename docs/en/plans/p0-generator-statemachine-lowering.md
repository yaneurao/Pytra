<a href="../../ja/plans/p0-generator-statemachine-lowering.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-generator-statemachine-lowering.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-generator-statemachine-lowering.md`

# P0: generator の EAST3 ステートマシン lowering

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-GENERATOR-LOWERING`

## 背景

Python の `yield` を使った generator 関数は、C++ emitter では list accumulation に lowering されているが、他の backend（PowerShell, Dart, Zig 等）では generator がサポートされていない。

EAST3 段階で generator をステートマシンに lowering すれば、全ターゲット言語で generator が動作する。

## 設計

generator 関数を以下の形に lowering:
1. 状態変数を持つ closure/class に変換
2. `yield` を状態遷移に変換
3. `next()` 呼び出しで次の値を返す

既存の C++ emitter の list accumulation 方式は、Python の generator 意味論（遅延評価）とは異なるが、結果が同じケースでは互換。

## 子タスク

- [ ] [ID: P0-GENERATOR-LOWERING-01] EAST3 で generator → ステートマシン lowering を設計する
- [ ] [ID: P0-GENERATOR-LOWERING-02] lowering パスを実装する
- [ ] [ID: P0-GENERATOR-LOWERING-03] ユニットテストを追加する

## 決定ログ

- 2026-03-22: PS 担当が yield_generator の動作不良を報告。全 backend 共通の改善として起票。難易度大。
