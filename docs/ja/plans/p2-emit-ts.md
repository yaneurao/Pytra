# P2-EMIT-TS: TypeScript emitter（JS とは別実装）

最終更新: 2026-03-26
ステータス: 未着手

## 背景

現行の TS emitter は JS emitter の出力を `.ts` 拡張子で保存しているだけで、型注釈がない。TypeScript のメリット（型安全性）が全く活かされていない。

## ポイント

### 1. 型注釈を出力する

EAST3 の `resolved_type` を TypeScript の型注釈として出力する。

```typescript
// 現行（JS コピー）
function escape_count(cx, cy, max_iter) {
    let x = 0.0;

// あるべき姿（TS）
function escape_count(cx: number, cy: number, max_iter: number): number {
    let x: number = 0.0;
```

型マッピング:

| EAST3 | TypeScript |
|---|---|
| `int8`〜`int64`, `uint8`〜`uint64` | `number` |
| `float32`, `float64` | `number` |
| `bool` | `boolean` |
| `str` | `string` |
| `None` | `void` (戻り値) / `null` (値) |
| `list[T]` | `T[]` |
| `dict[K,V]` | `Map<K, V>` or `Record<K, V>` |
| `tuple[T1,T2]` | `[T1, T2]` |
| `Any` / `Obj` | `any` |

### 2. TypeScript らしい出力

- `interface` / `class` の型定義を出力
- `const` / `let` の使い分け（再代入しない変数は `const`）
- アロー関数が適切な場面ではアロー関数を使う（lambda 等）
- `strict` mode を前提とした出力（`strictNullChecks` 対応）
- import は `.ts` 拡張子なし or `.js` 拡張子（TypeScript の規約に従う）

## 非対象

- JS emitter との共通化は目指さない。TS は独立した emitter として実装する
- JS emitter は型注釈なしの動的型付け向けとして維持する
