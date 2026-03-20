# P0: 整数 widening cast の冗長 emit 除去・narrowing cast の可読性改善

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-REDUNDANT-WIDENING-CAST-01`

## 背景

`src/runtime/cpp/generated/utils/png.cpp` に以下のコードが生成されている：

```cpp
for (uint8 b : pixels) {
    raw.append(int64(static_cast<int64>(b)));
}
```

これは三重に冗長：
1. 外側の `int64(...)` — `int64` のコンストラクタ呼び出し、不要
2. `static_cast<int64>(...)` — 明示キャスト、不要
3. `uint8 → int64` は C++ の暗黙の整数拡張（integral promotion）で自動変換される

正しくは `raw.append(b)` のみで十分。

## 原因

emitter（`type_bridge.py` の `_render_unbox_target_cast` / `apply_cast` / `_render_expr_kind_obj_str` 等）が
narrowing cast（大→小）と widening cast（小→大）を区別せず、算術型同士であれば
常に `static_cast` や `{t_norm}(static_cast<int64>(x))` を emit してしまっている。

具体的には `_render_unbox_target_cast` の int narrowing パス：
```python
return f"{t_norm}(static_cast<int64>({expr_txt}))"
```
が int64 ターゲットにも波及し、`int64(static_cast<int64>(b))` を生成している。

## 対象

- `src/toolchain/emit/cpp/emitter/type_bridge.py` — `_render_unbox_target_cast`
- `src/toolchain/emit/cpp/emitter/expr.py` — `apply_cast`
- `src/toolchain/emit/cpp/emitter/call.py` — `_render_builtin_static_cast_call`
- `src/runtime/cpp/generated/utils/png.cpp`（再生成で解消）

## 可読性問題（追加）

`static_cast<int64>(x)` は旧来の `py_to<int64>(x)` より**文字数が多く**可読性が下がっている：

| 形式 | 文字数 |
|------|--------|
| `py_to<int64>(x)` | 17 |
| `static_cast<int64>(x)` | 23 |
| `int64(x)` | 9 |

C++ では算術型同士のキャストに**関数形式キャスト（functional cast）**が使用可能。
`int64(x)` は `static_cast<int64>(x)` と完全に等価であり、Python の `int(x)` に近い見た目で読みやすい。

## 非対象

- object 境界フォールバック（`py_to_int64(obj_expr)` 等）— 型不明なので関数呼び出し形式維持
- `static_cast<bool>` — bool は functional cast と意味が異なるケースがあるため維持検討
- 非 C++ バックエンド

## 修正方針

**修正 1: widening cast を emit しない**

算術型同士の widening（ソース型のビット幅 ≤ ターゲット型、かつ値域が保存される方向）では cast を emit しない。

安全な widening（cast 不要）：
- `bool / uint8 / int8 / uint16 / int16 / uint32 / int32` → `int64`
- `bool / uint8 / int8 / uint16 / int16` → `int32` 等
- `float32` → `float64`

`apply_cast` / `_render_unbox_target_cast` に `_is_safe_widening_cast(src_t, dst_t)` ヘルパーを追加し、
widening の場合はキャスト式を生成しないようにする。ただし src_t が不明な場合は従来通り cast を emit する。

**修正 2: narrowing cast を `static_cast<T>` から `T(x)` 形式へ統一**

`apply_cast` / `_render_unbox_target_cast` で算術型への narrowing cast を
`static_cast<uint8>(static_cast<int64>(x))` → `uint8(x)` のように関数形式へ変更する。
`static_cast<int64>(x)` → `int64(x)` も同様。

## 受け入れ基準

- `int64(static_cast<int64>(b))` のようなパターンが生成コードに現れない。
- widening cast（uint8→int64 等）でキャスト式が emit されない（`b` のみ）。
- narrowing cast（int64→uint8 等）は `uint8(x)` 形式を emit する（`static_cast` 不使用）。
- `static_cast<int64>(x)` → `int64(x)` に統一されている。
- fixture 145/145・sample 18/18 pass、selfhost diff mismatches=0。
- png.cpp 再生成後に冗長 cast が消える。

## 決定ログ

- 2026-03-18: ユーザー指摘。`uint8 → int64` は C++ 暗黙変換で `static_cast` 不要。
  三重冗長（`int64(static_cast<int64>(b))`）として P0 に起票。
- 2026-03-18: ユーザー追記。`static_cast<int64>(x)` は `py_to<int64>(x)` より長く可読性が低下。
  narrowing cast も `uint8(x)` 形式に統一し、`static_cast` を算術キャストから排除する方針を追加。
- 2026-03-18: 実装完了。operator.py / expr.py / call.py / stmt.py / cpp_emitter.py / runtime_expr.py から算術型の `static_cast` 生成を除去し `T(x)` 形式に統一。enum/IntFlag の `static_cast<int64>(enum_val)` と PyObj ポインタキャストは C++ で必須なため維持。生成コード（sample/cpp, generated/）に `static_cast` 残存ゼロ。241 test pass。
