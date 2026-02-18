# TODO（未完了のみ）

## selfhost 回復（分解版）

1. [ ] `selfhost/py2cpp.py` のパース失敗を最小再現ケースへ分離する（`except ValueError:` 近傍）。
2. [ ] `src/common/east.py` self_hosted parser に不足構文を追加する。
3. [ ] 2. の再発防止として unit test を追加する。
4. [ ] `PYTHONPATH=src python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` を成功させる。
5. [ ] `selfhost/py2cpp.cpp` をコンパイルし、エラー件数を再計測する。
6. [ ] コンパイルエラー上位カテゴリを3分類し、順に削減する。
7. [ ] `selfhost/py2cpp.out` で `sample/py/01` を変換実行する。
8. [ ] `src/py2cpp.py` 実行結果との一致条件を定義し、比較確認する。

## 直近メモ

- 現状: `PYTHONPATH=src python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` で
  `unsupported_syntax: expected token EOF, got NAME`（`except ValueError:` 付近）により EAST 生成が停止。

## EAST へ移譲（py2cpp 簡素化・第2段）

1. [ ] `src/common/east_parts/core.py` で `Call(Name(...))` の `len/str/int/float/bool/min/max/Path/Exception` を全て `BuiltinCall` 化し、`py2cpp` の生分岐を削減する。
2. [ ] `src/common/east_parts/core.py` で `Attribute` 呼び出しの `owner_t == "unknown"` フォールバック依存を減らし、型確定時は EAST で runtime_call を確定させる。
3. [ ] `src/py2cpp.py` の `render_expr(kind=="Call")` から、EAST で吸収済みの `raw == ...` / `owner_t.startswith(...)` 分岐を段階削除する。
4. [ ] `test/unit/test_py2cpp_features.py` に `BuiltinCall` 正規化の回帰（`dict.get/items/keys/values`, `str` メソッド, `Path` メソッド）を追加する。
5. [ ] `test/unit` 一式を再実行し、`test/fixtures` 一括実行で退行がないことを確認する。
