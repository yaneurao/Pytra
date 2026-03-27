<a href="../../en/plans/p2-emit-ts.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

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

- **ジェネリクス**: EAST の `@template` → `function min<T>(a: T, b: T): T`
- **`const` / `let`**: EAST の `arg_usage: readonly` で判定。再代入しない変数は `const`
- **discriminated union**: EAST の nominal ADT → TS の discriminated union
  ```typescript
  type Maybe = { kind: "just"; value: number } | { kind: "nothing" };
  ```
- **union 型**: EAST の `UnionType` → `string | number`
- **optional 型**: EAST の `OptionalType` → `string | null`
- **型エイリアス**: Python の `type Scalar = int | float` → `type Scalar = number`
- **enum**: Python の `IntEnum` / `Enum` → TS の `enum`
- **interface / class**: dataclass → `interface`（データ構造）、メソッド付き → `class`
- **private / readonly**: クラスフィールドに適切なアクセス修飾子
- **`??` / `?.`**: None チェックパターン → nullish coalescing / optional chaining
- **アロー関数**: lambda → `(x) => x * 2`
- **strict mode**: `strictNullChecks` 対応を前提とした出力
- **import**: `.ts` 拡張子なし or `.js` 拡張子（TypeScript の規約に従う）

## JS との関係

TS emitter を正本とし、JS 出力は **型注釈を抑制したモード** として実装する。

```
pytra-cli2 -emit --target=ts  → 型注釈あり (.ts)
pytra-cli2 -emit --target=js  → 型注釈なし (.js)  ← 同じ emitter、型注釈を除去するだけ
```

- emitter は 1 つ（`toolchain2/emit/ts/`）
- JS/TS の挙動差がない（同じコード生成ロジック）
- `emit_ts_module(east3_doc, strip_types=False)` → TS
- `emit_ts_module(east3_doc, strip_types=True)` → JS
- 旧 JS emitter（`toolchain2/emit/js/`）は TS emitter 完成後に除去
