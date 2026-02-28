# P0: C++ `float64` cast 表記統一（`static_cast<float64>` → `float64(...)`）

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-FLOAT-CAST-STYLE-01`

背景:
- `sample/cpp` 出力には `float64 __hoisted_cast_4 = static_cast<float64>(width);` のような `float64` 変換が残っている。
- `float64` は runtime で `double` の alias であり、ここは可読性の観点で `float64(width)` の関数形式 cast へ寄せたい。
- 既存実装は `apply_cast`/emit 各所で `static_cast<...>` を使うため、型別に表記ポリシーを分離していない。

目的:
- C++ backend の `float64`（必要なら `float32` を含む）への数値 cast 表記を `float64(expr)` へ統一し、`static_cast<float64>(expr)` の出力を削減する。
- 意味保持を優先し、`object/Any/unknown` 境界や非浮動小数型 cast は既存 fail-closed を維持する。

対象:
- `src/hooks/cpp/emitter/expr.py`（`apply_cast`）
- `src/hooks/cpp/emitter/stmt.py` / `src/hooks/cpp/emitter/call.py` / `src/hooks/cpp/emitter/*` の `static_cast<float64>` 直接出力箇所
- `test/unit/test_east3_cpp_bridge.py` / `test/unit/test_py2cpp_codegen_issues.py` / `tools/check_py2cpp_transpile.py`
- `sample/cpp` 再生成確認（特に `16_glass_sculpture_chaos.cpp`）

非対象:
- `int64` / `uint8` / enum など `float64` 以外の cast 表記変更
- EAST3 の型推論仕様変更
- runtime の `using float64 = double;` 定義変更

受け入れ基準:
- `float64` への cast 表記が `float64(expr)` に統一され、`static_cast<float64>(...)` が新規出力されない。
- `object/Any/unknown` 境界の安全変換（`py_to<float64>` 等）は維持される。
- `check_py2cpp_transpile` と関連 unit が通る。
- `sample/cpp/16_glass_sculpture_chaos.cpp` の hoisted cast 例が `float64(width)` 形式へ変わる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`

決定ログ:
- 2026-02-28: ユーザー指示により、`static_cast<float64>(x)` の出力表記を `float64(x)` に統一する P0 タスクを起票した。
- 2026-02-28: 対象は「表記統一」であり、`float64` 変換そのもの（`int64 -> float64`）は維持する方針を確定した。

## 分解

- [ ] [ID: P0-CPP-FLOAT-CAST-STYLE-01-S1-01] C++ emitter の `float64` cast 出力箇所を棚卸しし、統一対象/除外対象を固定する。
- [ ] [ID: P0-CPP-FLOAT-CAST-STYLE-01-S2-01] `apply_cast` と直接出力箇所を `float64(expr)` 優先へ変更し、`static_cast<float64>` を排除する。
- [ ] [ID: P0-CPP-FLOAT-CAST-STYLE-01-S2-02] `object/Any/unknown` 経路で `py_to<float64>` 維持を確認する回帰テストを追加する。
- [ ] [ID: P0-CPP-FLOAT-CAST-STYLE-01-S3-01] transpile check / unit / sample 再生成で非退行を確認し、`sample/16` の該当出力差分を固定する。
