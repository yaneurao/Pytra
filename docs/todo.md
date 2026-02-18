# TODO（未完了のみ）

## selfhost 回復（分解版）

1. [x] `selfhost/py2cpp.py` のパース失敗を最小再現ケースへ分離する（`except ValueError:` 近傍）。
2. [x] `src/common/east.py` self_hosted parser に不足構文を追加する。
3. [x] 2. の再発防止として unit test を追加する。
4. [x] `PYTHONPATH=src python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` を成功させる。
5. [x] `selfhost/py2cpp.cpp` をコンパイルし、エラー件数を再計測する。
6. [x] コンパイルエラー上位カテゴリを3分類し、順に削減する。
7. [ ] `selfhost/py2cpp.out` で `sample/py/01` を変換実行する。
8. [x] `src/py2cpp.py` 実行結果との一致条件を定義し、比較確認する。
   - 一致条件: `sample/py/01` 入力に対して、`selfhost/py2cpp.out` と `python src/py2cpp.py` の生成 C++ がコンパイル可能で、実行出力（画像含む）が一致すること。
9. [x] `selfhost/` には `src` 最新をコピーしてよい前提で、`selfhost/py2cpp.py` と `selfhost/cpp_module/*` を同期する（`cp -f src/py2cpp.py selfhost/py2cpp.py` / `cp -f src/cpp_module/* selfhost/cpp_module/`）。
10. [x] `g++` ログ取得を `> selfhost/build.all.log 2>&1` に統一し、`stderr` 空でも原因追跡できるようにする。
11. [ ] selfhost 生成コードに残る Python 構文由来（`class ... : BaseEmitter`, `super().__init__`）を selfhost 対応表現へ置換する。
12. [ ] `object` / `std::any` 橋渡し不足を解消する（`make_object(std::any)` 相当、`dict<str, object>` 連携）。
13. [ ] `src/py2cpp.py` の `BaseEmitter` を「自己変換可能な最小型付き API」に整理し、`emit_stmt` 参照や `dict/object` 代入崩れを解消する。
14. [ ] `selfhost/py2cpp.out` を生成し、`sample/py/01_mandelbrot.py` を変換できるところまで到達する。
15. [ ] `selfhost/py2cpp.out` 生成結果と `python src/py2cpp.py` 生成結果の一致検証を実施する。

## object 制約の実装反映（汎用）

1. [x] EAST で `object` レシーバの属性アクセス・メソッド呼び出しを検出し、`unsupported_syntax` を返す。
2. [x] `py2cpp.py` の emit 時にもガードを追加し、`object` レシーバの呼び出し漏れを最終防止する。
3. [x] `test/fixtures/signature/` に `object` レシーバ呼び出し禁止の NG ケースを追加する。
4. [x] `test/unit` に NG ケースが失敗することを確認する回帰テストを追加する。

## 追加回帰（super）

1. [x] `super()` の回帰 fixture を追加する（`test/fixtures/oop/super_init.py`）。
2. [x] EAST parser 側で `super().__init__()` を含むコードが parse できる unit test を追加する。
3. [x] C++ 変換して実行まで通る runtime test を追加する（`test/unit/test_py2cpp_features.py`）。

## 直近メモ

- 進捗: `except ValueError:` を self_hosted parser で受理するよう修正し、EAST 生成は通過。
- 現在の主要原因（2026-02-18 再計測）:
  1. `selfhost/py2cpp.cpp` 冒頭の `BaseEmitter` 変換で型崩れが発生している（`dict<str, object> doc` への `make_object(east_doc)` 代入など）。
  2. `BaseEmitter.__init__(...)` が `BaseEmitter::__init__(self, ...)` として出力されるなど、Python メソッド呼び出し記法の漏れが残っている。
  3. `object` / `std::any` 混在のままメソッド呼び出しが出力され、`obj.get(...)` / `startswith(...)` などが C++ 型に落ちきっていない。
  4. 方針として selfhost 専用 lowering は極力増やさず、言語制約（`object` レシーバ呼び出し禁止）と型付き API への整理で汎用的に解消する。

## EAST へ移譲（py2cpp 簡素化・第2段）

1. [x] `src/common/east_parts/core.py` で `Call(Name(...))` の `len/str/int/float/bool/min/max/Path/Exception` を全て `BuiltinCall` 化し、`py2cpp` の生分岐を削減する。
2. [x] `src/common/east_parts/core.py` で `Attribute` 呼び出しの `owner_t == "unknown"` フォールバック依存を減らし、型確定時は EAST で runtime_call を確定させる。
3. [x] `src/py2cpp.py` の `render_expr(kind=="Call")` から、EAST で吸収済みの `raw == ...` / `owner_t.startswith(...)` 分岐を段階削除する。
4. [x] `test/unit/test_py2cpp_features.py` に `BuiltinCall` 正規化の回帰（`dict.get/items/keys/values`, `str` メソッド, `Path` メソッド）を追加する。
5. [x] `test/unit` 一式を再実行し、`test/fixtures` 一括実行で退行がないことを確認する。

## BaseEmitter 共通化（言語非依存 EAST ユーティリティ）

1. [x] `src/common/base_emitter.py` に言語非依存ヘルパ（`any_dict_get`, union型分解、`Any` 判定）を移し、`CppEmitter` の重複を削減する。
2. [x] ノード補助（`is_name/is_call/is_attr` などの軽量判定）を `BaseEmitter` に追加し、各エミッタの分岐可読性を上げる。
3. [x] 型文字列ユーティリティ（`is_list_type/is_dict_type/is_set_type`）を `BaseEmitter` へ寄せる。
4. [x] `py2cpp.py` で `BaseEmitter` の新規ユーティリティ利用へ置換し、挙動差分がないことを回帰テストで確認する。
5. [x] 次段として `py2rs.py` / `py2cs.py` でも流用可能な API 形に揃え、適用候補箇所を `todo.md` に追記する。
   - 候補: `get_expr_type` / `split_generic` / `split_union` / `is_*_type` / `is_call` / `is_attr`
