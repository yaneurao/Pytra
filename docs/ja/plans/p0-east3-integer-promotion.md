<a href="../../en/plans/p0-east3-integer-promotion.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: EAST3 で C++ 準拠の integer promotion を実装

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-INTEGER-PROMOTION`

## 背景

Python では小さい整数型（`int8`, `uint8`, `int16` 等）の演算結果は任意精度 `int` に昇格する。C/C++ にも同様の integer promotion ルールがある（`int` より小さい型は演算時に `int` に昇格）。

しかし EAST3 では演算結果の型昇格が行われず、emitter にそのまま渡される。integer promotion がない言語（Julia, Go, Rust, Zig, Swift）では、`uint8 << 9` がオーバーフローし不正な結果になる。

### 具体例

```python
# Python: bytes のイテレーション要素は int（任意精度）
for v in data:  # data: bytes, v: int
    bit_buffer |= v << bit_count  # 1 << 9 = 512 ✓
```

Julia では `UInt8(1) << 9 = 0`（オーバーフロー）になる。

### integer promotion がない言語

Julia, Go, Rust, Zig, Swift — これらの emitter で同種の問題が発生する。

## 設計

C/C++ と同じ integer promotion ルールを EAST3 lowering で適用する:

- `int8`, `uint8`, `int16`, `uint16` → 算術演算時に `int32` に昇格
- `int32` 以上はそのまま
- 演算結果の型を EAST3 ノードの `resolved_type` に反映する

emitter は EAST3 の型注釈を見てキャストコードを出すだけ:
- C++: キャスト不要（言語が同じ規則）
- Julia/Go/Rust/Zig/Swift: EAST3 の型注釈通りにキャスト挿入

## 対象

- `src/toolchain/compile/east2_to_east3_lowering.py` または新規パス — 算術演算ノードの型昇格

## 非対象

- 代入先型への縮小最適化（別タスク P1-INTEGER-PROMOTION-NARROWING で対応）
- 言語固有のオーバーフローセマンティクス

## 受け入れ基準

- [ ] EAST3 の算術演算ノードで `int8`/`uint8`/`int16`/`uint16` オペランドが `int32` に昇格される
- [ ] `bytes` イテレーション変数が `int32` 型に推論される
- [ ] promotion ルールのユニットテストが存在する
- [ ] 既存テストがリグレッションしない

## 子タスク

- [ ] [ID: P0-INTEGER-PROMOTION-01] EAST3 lowering に C++ 準拠の integer promotion パスを実装する
- [ ] [ID: P0-INTEGER-PROMOTION-02] `bytes`/`bytearray` イテレーション変数の型を `int32` に推論する
- [ ] [ID: P0-INTEGER-PROMOTION-03] ユニットテストを追加する
- [ ] [ID: P0-INTEGER-PROMOTION-04] 既存テストのリグレッションがないことを検証する

## 決定ログ

- 2026-03-21: Julia backend で `bytes` イテレーション時の `UInt8 << 9` オーバーフローが発覚。C++ の integer promotion と同じルールを EAST3 で統一的に適用する方針で起票。promotion がない言語（Julia, Go, Rust, Zig, Swift）全てで同種の問題が発生するため、emitter 個別対応ではなく EAST3 レベルで解決する。
