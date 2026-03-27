<a href="../../ja/plans/p0-disable-loop-invariant-hoist-passes.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-disable-loop-invariant-hoist-passes.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-disable-loop-invariant-hoist-passes.md`

# P0: ループ不変式 hoist 最適化パスを無効化

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-DISABLE-LOOP-HOIST`

## 背景

EAST3 optimizer に 2 つのループ不変式 hoist パスが存在する:

- `LoopInvariantCastHoistPass`: ループ内の数値キャスト（`float(height - 1)` 等）をループ外に `__hoisted_cast_N` として引き上げる
- `LoopInvariantHoistLitePass`: ループ先頭の不変代入文をループ外に引き上げる

これらの最適化は以下の理由で有害:

1. **ターゲット言語コンパイラが同じ最適化を行う** — C++/Dart/Zig/Julia 等のコンパイラは自前でループ不変式の巻き上げを行う
2. **合成変数名で可読性が壊れる** — `__hoisted_cast_1` のような名前は元ソースコードとの対応が不明
3. **トランスパイラ出力は可読性が重要** — 過剰な最適化は生成コードの可読性を損ない、デバッグを困難にする

## 対象

| ファイル | 変更内容 |
|---|---|
| `east3_opt_passes/__init__.py` | `LoopInvariantCastHoistPass` と `LoopInvariantHoistLitePass` を pass 列から除去 |

## 受け入れ基準

- [x] 2 つの loop hoist パスが optimizer pass 列に含まれない
- [x] 既存テストがリグレッションしない

## 子タスク

- [x] [ID: P0-DISABLE-LOOP-HOIST-01] `__init__.py` の pass 列から 2 パスを除去し、テスト検証する

## 決定ログ

- 2026-03-21: sample/dart/01_mandelbrot.dart で `__hoisted_cast_1` 等の合成変数がループ外に生成されていることを確認。ターゲット言語コンパイラが同等の最適化を行うため不要であり、可読性を損なうと判断。無効化を起票。
