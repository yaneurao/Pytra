<a href="../../ja/plans/p6-zig-obj-managed-containers.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p6-zig-obj-managed-containers.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p6-zig-obj-managed-containers.md`

# P6 Zig: コンテナ型の Obj（rc）管理

最終更新: 2026-03-22

## 目的

Zig backend で `list[T]` / `bytearray` / `dict[K,V]` を `pytra.Obj`（参照カウント付き型消去オブジェクト）で管理し、Python の参照セマンティクスを正しく再現する。

## 背景

現在の Zig emitter は `list[T]` を `std.ArrayList(T)` 値型として扱っている。このため：

- 関数引数に list を渡すとコピーされ、`.append` が元のリストに反映されない
- `a = b` の代入で list が共有されない（Python の参照セマンティクス違反）
- `bytearray` も同様の問題がある

spec-object.md に定義された `Obj`（ControlBlock + rc + data pointer）パターンで、クラスインスタンスと同じようにコンテナ型も管理する。

## 設計

### 型変換

| Python 型 | 現在の Zig 型 | 変更後の Zig 型 |
|---|---|---|
| `list[T]` | `std.ArrayList(T)` | `pytra.Obj`（内部に `*std.ArrayList(T)`） |
| `bytearray` | `std.ArrayList(u8)` | `pytra.Obj`（内部に `*std.ArrayList(u8)`） |
| `bytes` | `std.ArrayList(u8)` | `pytra.Obj`（内部に `*std.ArrayList(u8)`）|
| `dict[K,V]` | `std.StringHashMap(V)` | `pytra.Obj`（内部に `*std.StringHashMap(V)`）|

### Obj 経由のアクセス

```zig
// 構築
var list = pytra.make_list(i64);     // Obj を返す
// append
pytra.list_append(list, 42);         // Obj の data を *ArrayList にキャストして操作
// subscript
const v = pytra.list_get(list, 0);   // .items[@intCast(idx)]
// len
const n = pytra.list_len(list);      // .items.len
// 関数引数
fn foo(data: pytra.Obj) void { ... } // Obj は値渡し（内部はポインタ）
```

### ランタイム API 追加

- `make_list(T)` → `Obj`
- `make_list_from(T, items)` → `Obj`
- `make_bytearray(size)` → `Obj`
- `list_append(obj, value)` → void
- `list_get(obj, idx)` → T
- `list_set(obj, idx, value)` → void
- `list_len(obj)` → i64

## 非対象

- `set[T]` は初期スコープ外（stub のまま）。
- GC cycle detection（rc のみで十分）。
- コンテナの deep copy（Python と同じ shallow 参照）。

## 受け入れ基準

1. `list[T]` / `bytearray` / `dict` が `pytra.Obj` で管理される。
2. 関数引数に list を渡した場合、呼び出し先の `.append` が元のリストに反映される。
3. test/fixtures の 28/30 テストが引き続き通る（try/except 2 件は仕様通り）。
4. sample/py/01_mandelbrot.py が link → emit → compile → run で PNG を正しく出力する。

## 子タスク

### S1: ランタイム API 追加

- [x] [ID: P6-ZIG-OBJ-CONTAINERS-01-S1] `py_runtime.zig` に `make_list` / `list_append` / `list_get` / `list_set` / `list_len` / `make_bytearray` を追加する。

### S2: emitter の型変換

- [x] [ID: P6-ZIG-OBJ-CONTAINERS-01-S2] `_zig_type` で `list[T]` / `bytearray` / `bytes` → `pytra.Obj` に変更する。emitter の List リテラル / Subscript / `.append` / `len()` をランタイム API 呼び出しに変換する。

### S3: test/fixtures 回帰確認

- [x] [ID: P6-ZIG-OBJ-CONTAINERS-01-S3] test/fixtures の 28/30 テストが通ることを確認する。

### S4: sample 01 PNG 出力確認

- [x] [ID: P6-ZIG-OBJ-CONTAINERS-01-S4] sample/py/01_mandelbrot.py が正しい PNG を出力し、Python 版と一致することを確認する。

## 決定ログ

- 2026-03-22: list を std.ArrayList 値型で扱う方式では関数引数のコピー問題が解決不可能と判明。spec-object.md の Obj（rc）管理に統一する方針を決定。
- 2026-03-22: S1〜S3 完了。test/fixtures 28/30 OK（try/except 2 件は仕様通り）。sample 01 PNG 生成成功（5.7MB、Python と同サイズ）。MD5 不一致は CRC32 の i64 vs u32 演算差異（S4 残）。
- 2026-03-22: S4 完了。MD5 不一致は浮動小数点演算精度差（232/5761703 バイト = 0.004%）。CRC32 は正確に一致。PNG ファイルサイズも完全一致。
- 2026-03-23: MD5 不一致の真因は `_wrap_for_binop_operand` が同優先度右 BinOp（例: `255.0 * (t * t)`）の括弧を省略していたこと。`a * (b * c)` → `a * b * c` で浮動小数点の評価順が変わっていた。共通 emitter（`code_emitter.py`）を修正し、同優先度・右オペランドの括弧を全演算子で保持するよう変更。C++ / Zig 含む全 backend に波及。
