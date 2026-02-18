# TODO（未完了のみ）

## selfhost 回復（分解版）

1. [ ] `selfhost/py2cpp.cpp` で `object -> optional<dict<...>> / list<object> / str` 代入が失敗している箇所を、`any_to_dict/any_to_list/any_to_str` を通る形へ統一する。
2. [ ] `py_dict_get_default(...)` 呼び出しの曖昧解決（`bool` 既定値など）を解消するため、`dict_get_bool/str/list/node` など型付き helper 呼び出しへ置換する。
3. [ ] `emit_stmt` / `emit_assign` / `render_expr` の `dict|None` 固定引数を段階的に `Any` 受け + 内部 `dict` 化へ寄せ、selfhost 生成コードの `std::any` 入力と整合させる。
4. [ ] `cpp_type` へ `str|None` 等が流入した際の `object` 退避を見直し、不要な `object` 経由変換を減らす。
5. [ ] `selfhost/py2cpp.cpp` の先頭 500 行を重点レビューし、`BaseEmitter` 起点のエラー（型境界）を 0 件にする。
6. [ ] `selfhost/py2cpp.out` を生成する。
7. [ ] `selfhost/py2cpp.out sample/py/01_mandelbrot.py` 実行を通す。
8. [ ] `selfhost/py2cpp.out` 生成結果と `python src/py2cpp.py` 生成結果の一致検証を実施する。

## 直近メモ

- 進捗: `except ValueError:` 受理と `return`（値なし）受理を self_hosted parser に追加し、EAST 生成は通過。
- 現在の主要原因（2026-02-18 再計測）:
  1. `BaseEmitter.any_dict_get` が `optional<dict>` に対して `.find/.end` を生成してしまう。
  2. `Any -> object` 変換の影響で、`""` / `list{}` / `nullopt` を default 引数に渡す箇所が大量に不整合化している。
  3. `render_expr` 系 API が `dict|None` 固定のため、selfhost 生成側で `object/std::any` から呼び出した時に詰まる。
  4. 方針として selfhost 専用 lowering は極力増やさず、型付き helper と runtime 補助 API の拡充で汎用的に解消する。
- 更新（2026-02-18）:
  1. `BaseEmitter` 側の `any_*` を明示 `if` へ書き換え、ifexp（三項演算子）由来の不整合を削減する下準備を実施。
  2. `selfhost/py2cpp.py` と `selfhost/cpp_module/*` を `src` 最新へ同期済み。
  3. 依然として主因は `object` / `optional<dict>` / `std::any` の境界変換（代入・引数渡し・`py_dict_get_default` 呼び出し）に集中している。
