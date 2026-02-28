# P0: C++ `float64` 同士の除算で `py_div` を使わず `/` を直接出力する

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-DIV-FLOAT-FASTPATH-01`

背景:
- 現行 C++ emitter は `Div`（`/`）をほぼ一律で `py_div(lhs, rhs)` へ lower している。
- `py_div` は Python 互換の「真の除算」経路として必要だが、`float64` 同士の演算では実質 `lhs / rhs` と同じになり、生成コード可読性が下がる。
- `sample/cpp/01_mandelbrot.cpp` でも `float64` 同士の式が `py_div(...)` になっている。

目的:
- 型が `float64`（または `float32`）同士で確定している `Div` は、C++ 出力で `lhs / rhs` を直接使う。
- cast 適用後に float 同士へ昇格する経路（`int/int`・`float/int` 含む）も `/` 直接出力へ寄せる。
- unknown/object など型未確定経路は `py_div` を維持し、fail-closed を保つ。

対象:
- `src/hooks/cpp/emitter/operator.py`（`Div` lower 判定）
- 必要なら `src/hooks/cpp/optimizer/passes/*`（後段補助）
- `test/unit/test_py2cpp_smoke.py` / `test/unit/test_east3_cpp_bridge.py` / `tools/check_py2cpp_transpile.py`
- `sample/cpp` 再生成結果（特に `01_mandelbrot.cpp`）

非対象:
- `FloorDiv` / `Mod` の意味仕様変更
- EAST3 共通最適化層への移管
- Rust/Java/他 backend の Div lower 変更

受け入れ基準:
- `float64/float64`（必要なら `float32` 含む）で型確定した `Div` は `py_div` ではなく `/` が出力される。
- cast 適用後に float 同士となる `Div`（`int/int`・`float/int` を含む）も `/` へ縮退される。
- unknown/object 経路では `py_div` を維持し、Python 互換を壊さない。
- `check_py2cpp_transpile` と C++ smoke が非退行で通る。
- `sample/cpp/01_mandelbrot.cpp` の該当行（`t` 計算）が `/` 表記へ変わる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_smoke.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`
- `rg -n "py_div\\(| / " sample/cpp/01_mandelbrot.cpp`

決定ログ:
- 2026-02-28: ユーザー指示により、`float64` 同士の `Div` で `py_div` を使わない C++ 出力最適化を `P0` で起票した。
- 2026-02-28: `Div` の実効型は `get_expr_type()` だけでなく `casts`（`on=left/right`, `to=float64/float32`）を反映して判定し、型昇格済み経路も `/` へ縮退する方針にした。
- 2026-02-28: unknown/object は従来どおり `py_div` を維持し、fastpath 未適用時は fail-closed を守る方針にした。

## 分解

- [x] [ID: P0-CPP-DIV-FLOAT-FASTPATH-01-S1-01] `Div` lower の型条件（`float64/float64` 優先、Any/object/int は `py_div` 維持）を文書化する。
- [x] [ID: P0-CPP-DIV-FLOAT-FASTPATH-01-S2-01] `operator.py` の `Div` 分岐へ typed fastpath（`/` 直接出力）を実装する。
- [x] [ID: P0-CPP-DIV-FLOAT-FASTPATH-01-S2-02] `float32` / mixed float / int / Any/object の境界ケースを回帰テストで固定する。
- [x] [ID: P0-CPP-DIV-FLOAT-FASTPATH-01-S3-01] `check_py2cpp_transpile` / C++ smoke を通し、非退行を確認する。
- [x] [ID: P0-CPP-DIV-FLOAT-FASTPATH-01-S3-02] `sample/cpp` を再生成し、`01_mandelbrot.cpp` で `py_div` 縮退を確認する。
