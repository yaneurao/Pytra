# TODO（未完了のみ）

## selfhost 回復（分解版）

1. [ ] `BaseEmitter.any_dict_get` を `dict.get` ベースへ置換し、`optional<dict>` で `.find/.end` が出ないようにする。
2. [ ] `BaseEmitter.any_to_dict/any_to_list/any_to_str` の自己変換を明示 `if` 文へ書き換え、三項演算子の型衝突（`object` vs `nullopt`）を解消する。
3. [ ] `CppEmitter` 内の `any_dict_get(..., "", list{}, nullopt)` 呼び出しを、型付き helper（`dict_get_str/list/node`）へ段階置換する。
4. [ ] `cpp_type` へ `str|None` 入力を渡す経路を整理し、`cpp_type(object)` への暗黙流入を止める。
5. [ ] `emit_stmt` / `emit_assign` / `render_expr` など主要 API の引数型を selfhost でも崩れにくい形（`Any` 受け + 内部で `dict` 化）に統一する。
6. [ ] `py_runtime.h` に不足している `object/list` ブリッジ（`obj_to_list_ptr` 相当、`py_join(object)`）を実装し、selfhost生成コードの補助 API を揃える。
7. [ ] `selfhost/py2cpp.cpp` の先頭 400 行を再レビューし、`BaseEmitter` 起点のコンパイルエラーを 0 にする。
8. [ ] `selfhost/py2cpp.out` を生成する。
9. [ ] `selfhost/py2cpp.out sample/py/01_mandelbrot.py` 実行を通す。
10. [ ] `selfhost/py2cpp.out` 生成結果と `python src/py2cpp.py` 生成結果の一致検証を実施する。

## 直近メモ

- 進捗: `except ValueError:` 受理と `return`（値なし）受理を self_hosted parser に追加し、EAST 生成は通過。
- 現在の主要原因（2026-02-18 再計測）:
  1. `BaseEmitter.any_dict_get` が `optional<dict>` に対して `.find/.end` を生成してしまう。
  2. `Any -> object` 変換の影響で、`""` / `list{}` / `nullopt` を default 引数に渡す箇所が大量に不整合化している。
  3. `render_expr` 系 API が `dict|None` 固定のため、selfhost 生成側で `object/std::any` から呼び出した時に詰まる。
  4. 方針として selfhost 専用 lowering は極力増やさず、型付き helper と runtime 補助 API の拡充で汎用的に解消する。
