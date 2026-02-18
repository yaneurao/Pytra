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
9. [ ] `tools/selfhost_error_report.py` の分類結果に基づき、`keyword_collision` を 0 件化する。
10. [ ] `tools/selfhost_error_report.py` の分類結果に基づき、`object_any_mismatch` を 0 件化する。
11. [ ] `tools/selfhost_error_report.py` の分類結果に基づき、`dict_attr_access_mismatch` を 0 件化する。
12. [ ] `tools/selfhost_error_report.py` の分類結果で `other` を段階的に削減する。
13. [ ] selfhost 生成コードに残る Python 構文由来（`class ... : BaseEmitter`, `super().__init__`）を selfhost 対応表現へ置換する。

## 直近メモ

- 進捗: `except ValueError:` を self_hosted parser で受理するよう修正し、EAST 生成は通過。
- 現状の selfhost コンパイル上位3カテゴリ:
  1. C++予約語衝突（例: `default` という引数名がそのまま出力される）
  2. `object` / `std::any` 混在時の型崩れ（`dict<str, object>` へ不整合代入）
  3. `make_object(std::any)` など selfhost 生成コードの型変換不足
- `python3 tools/selfhost_error_report.py selfhost/build.stderr.log`（2026-02-18）:
  - `total_errors=570`
  - `keyword_collision=4`
  - `object_any_mismatch=48`
  - `other=518`
- 追加ブロッカー（2026-02-18 再計測）:
  - `selfhost/py2cpp.cpp` に `BaseEmitter` 継承や `super().__init__` が残り、C++ 生成として不正。

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
