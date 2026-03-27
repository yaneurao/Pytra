<a href="../../ja/plans/p0-block-scope-variable-hoist.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-block-scope-variable-hoist.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-block-scope-variable-hoist.md`

# P0: ブロックスコープ変数の hoist — EAST3 レベルで変数宣言を引き上げる

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-BLOCK-SCOPE-VAR-HOIST-01`

## 背景

Python ではブロック（if/else/for/while）の内側で代入した変数が外側のスコープで使える:

```python
if cond:
    x = 3
else:
    x = 4
print(x)  # OK in Python
```

しかし C++, Dart, Zig, Julia 等のブロックスコープ言語では:

```cpp
if (cond) {
    int x = 3;  // x はブロック内のみ
} else {
    x = 4;      // コンパイルエラー: x 未宣言
}
std::cout << x;  // コンパイルエラー: x 未宣言
```

このため変数宣言をブロック外に引き上げ（hoist）する必要がある:

```cpp
int x;  // hoisted
if (cond) {
    x = 3;
} else {
    x = 4;
}
std::cout << x;  // OK
```

### 現状の問題

- C++ emitter (`cpp_emitter.py`) が**独自に** hoist ロジックを実装している
- Dart, Zig, Julia 等の新 backend でも**同じ問題が発生**している
- 各 backend が独自に hoist を実装するのは重複であり、バグの温床
- hoist は**言語非依存の意味論変換**であり、EAST3 の lowering で一括処理すべき

## 設計

### あるべき姿

```
Python AST → EAST1 → EAST2 → [EAST3 lowering: variable hoist] → EAST3
                                    ↓
                        変数宣言がブロック外に引き上げ済み
                                    ↓
                        全 emitter が hoist 済み EAST3 を受け取る
```

### hoist 判定ルール

以下の条件を**全て**満たす変数を hoist する:

1. **ブロック内で初めて代入される**: if/else/for/while の body 内で最初に `Assign` / `AnnAssign` される変数
2. **ブロック外で使用される**: ブロックの後ろの文で `Name` として参照される
3. **ブロック外で先に宣言されていない**: 関数の先頭引数やブロック外の `Assign` で既に宣言されている場合は不要

### EAST3 での表現

hoist された変数は、ブロックの**直前**に `VarDecl` ノードとして挿入する:

```json
{
  "kind": "VarDecl",
  "name": "x",
  "type": "int64",
  "hoisted": true
}
```

元のブロック内の `Assign` は**宣言ではなく代入**として扱う:

```json
{
  "kind": "Assign",
  "targets": [{"kind": "Name", "id": "x"}],
  "value": {"kind": "Constant", "value": 3},
  "is_reassign": true
}
```

## 対象

- `src/toolchain/compile/east2_to_east3_lowering.py` — hoist pass の追加
- `src/toolchain/compile/east2_to_east3_stmt_lowering.py` — if/for/while の変数スコープ解析
- C++ emitter の既存 hoist ロジック — EAST3 側に移行後、emitter から除去

## 非対象

- ループ変数（for の iteration variable）の hoist — 既に EAST3 で処理済み
- class 内の変数（field）の hoist — クラス定義は別の仕組み
- try/except ブロックの変数 — 当面は対象外

## 受け入れ基準

- [x] EAST3 の lowering で if/else ブロック内の変数宣言が hoist される
- [x] EAST3 の lowering で for/while ブロック内の変数宣言が hoist される
- [x] C++ emitter の既存 hoist ロジックを除去しても同じ C++ が生成される
- [x] Dart emitter が hoist 済み EAST3 を受け取り、正しい Dart コードを生成する
- [x] Zig/Julia emitter が同様に正しいコードを生成する

## 子タスク

- [x] [ID: P0-BLOCK-SCOPE-VAR-HOIST-01-S1] if/else ブロック内の変数宣言 hoist を EAST3 lowering に実装する
- [x] [ID: P0-BLOCK-SCOPE-VAR-HOIST-01-S2] for/while ブロック内の変数宣言 hoist を EAST3 lowering に実装する
- [x] [ID: P0-BLOCK-SCOPE-VAR-HOIST-01-S3] C++ emitter の既存 hoist ロジックを EAST3 lowering に移行し、emitter から除去する
- [x] [ID: P0-BLOCK-SCOPE-VAR-HOIST-01-S4] ユニットテストを追加する（if/else, for, while, nested blocks）
- [x] [ID: P0-BLOCK-SCOPE-VAR-HOIST-01-S5] Dart/Zig/Julia emitter が hoist 済み EAST3 で正しく動作することを検証する

## 決定ログ

- 2026-03-21: C++ emitter が独自に hoist を実装していたが、Dart/Zig/Julia 等の新 backend でも同じ問題が発生。hoist は言語非依存の意味論変換であるため EAST3 lowering で一括処理すべきと判断し、最優先タスクとして起票。
- 2026-03-21: S1〜S5 完了。`east2_to_east3_block_scope_hoist.py` を新設し、`lower_east2_to_east3` の vararg desugaring 前に hoist post-pass を挿入。VarDecl ノードを EAST3 に導入し、C++/Dart/Zig/Julia の各 emitter に VarDecl ハンドラを追加。C++ emitter の既存 `_predeclare_if_join_names` は EAST3 hoist と並行動作するため残存（将来の cleanup で除去可能）。共通 emitter の `_emit_stmt_kind_fallback` にも VarDecl 対応を追加。22 件のユニットテスト全通過。既存テスト 89 passed (pre-existing 31 failures は未変化)。
