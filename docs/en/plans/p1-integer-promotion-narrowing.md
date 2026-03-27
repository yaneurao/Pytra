<a href="../../ja/plans/p1-integer-promotion-narrowing.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p1-integer-promotion-narrowing.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p1-integer-promotion-narrowing.md`

# P1: integer promotion の代入先型縮小最適化

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-INTEGER-PROMOTION-NARROWING`

## 背景

P0-INTEGER-PROMOTION で EAST3 に C++ 準拠の integer promotion が導入されると、`uint8` の演算結果が `int32` に昇格される。しかし代入先が `int16` 等の小さい型の場合、素朴な lowering では不要な中間キャストが発生する:

```
// 素朴な lowering
int16 result = int16(int32(u) << 1)

// 最適化後
int16 result = int16(u) << 1
```

代入先の型が演算の精度要求を満たすなら、promotion 先を代入先型に縮小できる。

## 設計

EAST3 の代入文で、代入先の型が promotion 後の型より小さい場合:
1. 代入先型がオペランドの元型以上なら、promotion 先を代入先型に縮小
2. オペランドを代入先型にキャストし、演算を代入先型で実行
3. 中間の `int32` キャストを除去

## 受け入れ基準

- [ ] `int16 x = u8_val << 1` で `int32` 経由のキャストが生成されない
- [ ] 最適化の正当性テスト（オーバーフロー境界ケース含む）

## 子タスク

- [ ] [ID: P1-INTEGER-PROMOTION-NARROWING-01] EAST3 optimizer に代入先型縮小パスを実装する
- [ ] [ID: P1-INTEGER-PROMOTION-NARROWING-02] ユニットテストを追加する

## 決定ログ

- 2026-03-21: P0-INTEGER-PROMOTION の設計議論中に最適化案として起票。EAST3 の型情報が揃っていれば機械的に判定可能。
