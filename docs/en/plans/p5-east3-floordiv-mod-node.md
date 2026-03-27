<a href="../../ja/plans/p5-east3-floordiv-mod-node.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p5-east3-floordiv-mod-node.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p5-east3-floordiv-mod-node.md`

# P5: FloorDiv / Mod を EAST3 IR ノード化し py_runtime.h から除去

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P5-EAST3-FLOORDIV-MOD-NODE-01`

## 背景

`py_floordiv` / `py_mod` / `py_div` は現在 `src/runtime/cpp/native/core/py_runtime.h` に実装され、C++ バックエンドの `src/toolchain/emit/cpp/emitter/operator.py` が文字列リテラルとして直接 emit している。

問題：
- EAST3 IR ノードとして表現されていないため、各言語バックエンドが意味論を独自に保持するか C++ ヘルパを移植する必要がある。
- 特に `py_floordiv` / `py_mod` は言語間で挙動が大きく異なる（Python は floor 丸め、C++ は truncation 丸め、Go / Rust / JS も各自仕様が異なる）。
- 現状の C++ emitter は `py_floordiv(lhs, rhs)` を emit するだけで、他バックエンドがこれを参照できない。

## 目的

- C++ emitter が `py_floordiv`/`py_mod` を EAST3 の BinOp ノード（`FloorDiv`/`Mod`）から直接インライン C++ コードに変換するよう変更する。
- `py_floordiv` / `py_mod` を `py_runtime.h` から除去し、py_runtime.h を縮小する。
- 各非 C++ バックエンドが同じ BinOp ノードから言語ネイティブな floor 除算・modulo を生成できる基盤を整備する。

## 対象

- `src/toolchain/emit/cpp/emitter/operator.py`（FloorDiv / Mod / Div の emit）
- `src/runtime/cpp/native/core/py_runtime.h`（`py_div` / `py_floordiv` / `py_mod` 除去）
- `test/unit/toolchain/emit/cpp/`（回帰テスト）
- `docs/ja/spec/spec-runtime.md`（変更点注記）

## 非対象

- EAST3 IR ノード定義そのもの（FloorDiv / Mod は既存 BinOp として表現済みと想定）
- 非 C++ バックエンドへの実装（基盤整備のみ、実際の多言語 emit は後続タスク）
- `py_div`（真除算）は意味論が言語間で比較的一致するため優先度低（確認後に判断）

## 受け入れ基準

- C++ emitter が `py_floordiv` / `py_mod` 呼び出しを生成せず、インライン式（整数: floor 演算付き、浮動小数: `std::floor(a/b)`）を emit する。
- Python の floor 丸め仕様（負数時の符号挙動）を C++ インライン式で再現できている。
- `py_floordiv` / `py_mod` が `py_runtime.h` から削除されており、ヘッダ参照が消えている。
- fixture 3/3・sample 18/18 pass、selfhost diff mismatches=0。

## 子タスク（案）

- [ ] [ID: P5-EAST3-FLOORDIV-MOD-NODE-01-S1-01] `operator.py` における FloorDiv / Mod / Div の emit 経路を調査し、EAST3 ノードとの対応・インライン化安全条件を確認する。
- [ ] [ID: P5-EAST3-FLOORDIV-MOD-NODE-01-S2-01] C++ emitter の FloorDiv / Mod emit を `py_floordiv`/`py_mod` 呼び出しからインライン C++ 式（整数・float 分岐）に切り替える。
- [ ] [ID: P5-EAST3-FLOORDIV-MOD-NODE-01-S2-02] `py_floordiv` / `py_mod` を `py_runtime.h` から削除し、コンパイル・テストが通ることを確認する。
- [ ] [ID: P5-EAST3-FLOORDIV-MOD-NODE-01-S3-01] fixture / sample / selfhost で非退行を確認し、ドキュメントを更新する。

## 決定ログ

- 2026-03-18: P5-ANY-ELIM-OBJECT-FREE-01 完了後に py_runtime.h 縮小・多言語対応容易化の観点で起票。`operator.py` が `py_floordiv(lhs, rhs)` / `py_mod(lhs, rhs)` を文字列 emit しており EAST3 IR との接続がないことを確認。`py_div` は真除算で言語間差異が小さいため後回し方針。
