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

- [ ] [ID: P6-ZIG-OBJ-CONTAINERS-01-S1] `py_runtime.zig` に `make_list` / `list_append` / `list_get` / `list_set` / `list_len` / `make_bytearray` を追加する。

### S2: emitter の型変換

- [ ] [ID: P6-ZIG-OBJ-CONTAINERS-01-S2] `_zig_type` で `list[T]` / `bytearray` / `bytes` → `pytra.Obj` に変更する。emitter の List リテラル / Subscript / `.append` / `len()` をランタイム API 呼び出しに変換する。

### S3: test/fixtures 回帰確認

- [ ] [ID: P6-ZIG-OBJ-CONTAINERS-01-S3] test/fixtures の 28/30 テストが通ることを確認する。

### S4: sample 01 PNG 出力確認

- [ ] [ID: P6-ZIG-OBJ-CONTAINERS-01-S4] sample/py/01_mandelbrot.py が正しい PNG を出力し、Python 版と一致することを確認する。

## 決定ログ

- 2026-03-22: list を std.ArrayList 値型で扱う方式では関数引数のコピー問題が解決不可能と判明。spec-object.md の Obj（rc）管理に統一する方針を決定。
