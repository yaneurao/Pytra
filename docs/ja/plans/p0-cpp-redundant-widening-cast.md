# P0: 整数 widening cast の冗長 emit 除去

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

- `src/backends/cpp/emitter/type_bridge.py` — `_render_unbox_target_cast`
- `src/backends/cpp/emitter/expr.py` — `apply_cast`
- `src/backends/cpp/emitter/call.py` — `_render_builtin_static_cast_call`
- `src/runtime/cpp/generated/utils/png.cpp`（再生成で解消）

## 非対象

- narrowing cast（int64 → uint8 等）— 引き続き明示キャストが必要
- object 境界フォールバック — 型が不明なので static_cast 維持
- 非 C++ バックエンド

## 修正方針

算術型同士の widening（ソース型のビット幅 ≤ ターゲット型のビット幅、かつ符号が拡張方向）では
cast を emit しない。

C++ の widening 規則（主要な安全な変換）：
- `bool / uint8 / int8 / uint16 / int16 / uint32 / int32` → `int64` : 安全な widening
- `bool / uint8 / int8 / uint16 / int16` → `int32` 等 : 同様
- `float32` → `float64` : widening
- 符号付き→符号なし（同ビット幅以上）: 厳密には value-preserving ではないが、Python の意味論上は正しいキャストが必要なため対象外

`apply_cast` / `_render_unbox_target_cast` に `_is_safe_widening_cast(src_t, dst_t)` ヘルパーを追加し、
widening の場合はキャスト式を生成しないようにする。

## 受け入れ基準

- `int64(static_cast<int64>(b))` のようなパターンが生成コードに現れない。
- widening cast（uint8→int64 等）で cast 式が emit されない（`b` のみ）。
- narrowing cast（int64→uint8 等）は引き続き `uint8(static_cast<int64>(x))` を emit する。
- fixture 145/145・sample 18/18 pass、selfhost diff mismatches=0。
- png.cpp 再生成後に冗長 cast が消える。

## 決定ログ

- 2026-03-18: ユーザー指摘。`uint8 → int64` は C++ 暗黙変換で `static_cast` 不要。
  三重冗長（`int64(static_cast<int64>(b))`）として P0 に起票。
