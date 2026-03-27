<a href="../../ja/plans/p4-integer-promotion-operand-cast.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p4-integer-promotion-operand-cast.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p4-integer-promotion-operand-cast.md`

# P4: integer promotion をオペランドキャストに変更

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P4-INTEGER-PROMOTION-OPERAND-CAST`

## 背景

P0-INTEGER-PROMOTION で EAST3 の算術演算に C++ 準拠の integer promotion を導入した。しかし現在の実装は BinOp/UnaryOp の `resolved_type` を書き換えるだけで、EAST2→3 lowering が挿入する `Unbox` ノードが結果を外側からキャストする形になっている:

```
// 現状 (result cast): int16(int8(-128) - 1)
Assign(target=b:int16)
  value: Unbox(int16)
    value: BinOp(resolved_type=int64)
      left: Name a (int8)
      right: Constant 1 (int64)
```

これは C++ では暗黙 promotion があるため正しく動くが、promotion がない言語（Julia, Go, Zig, Rust, Swift）ではオペランドが元の型のまま計算され、オーバーフローする:

- `int8(-128) - 1` → int8 で計算 → overflow → `+127` (WRONG)
- `int16(-128) - 1` → `-129` (CORRECT)

正しい EAST3 表現:

```
// 正しい (operand cast): int16(a) - 1
Assign(target=b:int16)
  value: BinOp(resolved_type=int16)
    left: Cast(a, int32)   ← オペランドをキャスト
    right: Constant 1
```

## 設計

integer promotion パスで、BinOp/UnaryOp のオペランドが小さい整数型の場合:
1. オペランドを `Cast` ノードで promoted 型にキャストする
2. BinOp の `resolved_type` を promoted 型に設定する
3. 外側の `Unbox` が不要になる場合は除去する（narrowing と組み合わせ）

## 対象

| ファイル | 変更内容 |
|---|---|
| `east2_to_east3_integer_promotion.py` | オペランドに Cast ノードを挿入する |

## 受け入れ基準

- [ ] `int8(-128) - 1` で BinOp のオペランドが promoted 型にキャストされる
- [ ] `uint8(1) << 9` で左オペランドが int32 にキャストされる
- [ ] 外側の Unbox が不要な場合に除去される
- [ ] 既存テストがリグレッションしない

## 子タスク

- [ ] [ID: P4-INTEGER-PROMOTION-OPERAND-CAST-01] promotion パスで小さい整数型オペランドに Cast ノードを挿入する
- [ ] [ID: P4-INTEGER-PROMOTION-OPERAND-CAST-02] 不要な Unbox を除去する
- [ ] [ID: P4-INTEGER-PROMOTION-OPERAND-CAST-03] ユニットテストを有効化し、リグレッション検証する

## 決定ログ

- 2026-03-21: `int8(-128) - 1` のオーバーフロー例で、result cast ではなく operand cast が必要と判断。promotion がない言語で演算が元の型のまま行われることが原因。
