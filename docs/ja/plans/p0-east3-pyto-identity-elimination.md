# P0: EAST3 同型 `py_to<T>` 縮退（最優先）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-EAST3-PYTO-IDENTITY-01`

背景:
- C++ 出力に `py_to<float64>(x)` のような「入力が既に `float64` と確定している変換」が残る経路がある。
- これは意味的には no-op だが、生成コードの可読性を下げ、不要なランタイム変換呼び出しに見えるノイズを作る。
- 既存の C++ 側同型 cast 省略は局所的で、前段（EAST3）での一貫した縮退規約が不足している。

目的:
- EAST3 最適化層で同型 `py_to<T>` を先に削減し、backend 非依存で冗長変換を縮退する。
- C++ emitter には fail-closed な最終ガードのみ残し、責務を「EAST3優先 + emitter安全網」に整理する。

対象:
- `src/pytra/compiler/east_parts/east3_opt_passes/*`（同型変換縮退 pass）
- `src/pytra/compiler/east_parts/east3_optimizer.py`（pass 順序/有効化）
- `src/hooks/cpp/emitter/*`（最終ガードの最小化・再発防止）
- `test/unit/test_east3_optimizer.py` / `test/unit/test_east3_cpp_bridge.py` / `tools/check_py2cpp_transpile.py`

非対象:
- `object`/`Any`/`unknown` など動的経路の変換仕様変更
- `py_to` runtime API 自体の契約変更
- C++ 以外 backend のコード整形改善

受け入れ基準:
- EAST3 で source/target が同型と確定する `py_to<T>` 相当 cast は、意味保存の範囲で除去される。
- `object`/`Any`/`unknown` 経路では cast を維持し、fail-closed を保つ。
- C++ emitter 側は再発防止の最終ガードとして同型 cast を抑止できる。
- `check_py2cpp_transpile` と関連 unit が通り、回帰がない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`

決定ログ:
- 2026-02-28: ユーザー指示により、`py_to<float64>(x)` のような同型変換削減は「EAST3最適化層を主担当、C++ emitter を安全網」とする方針を確定した。
- 2026-03-01: `IdentityPyToElisionPass` を追加し、`py_to_string/py_to_bool/py_to_int64/py_to_float64/static_cast` と `Unbox/CastOrRaise` の同型変換を EAST3 側で縮退する規約を実装した（`object/Any/unknown` は除外）。
- 2026-03-01: `build_default_passes()` へ新 pass を追加し、`test_east3_optimizer.py` に pass 有効/無効検証と `py_to_string` / `Unbox` の縮退回帰を追加した。
- 2026-03-01: `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v`、`PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`、`python3 tools/check_py2cpp_transpile.py`、`python3 tools/regenerate_samples.py --langs cpp --force` を実行して非退行を確認した。

## 分解

- [x] [ID: P0-EAST3-PYTO-IDENTITY-01-S1-01] 同型 `py_to<T>` 縮退規約（適用条件/除外条件）を EAST3 pass 仕様として固定する。
- [x] [ID: P0-EAST3-PYTO-IDENTITY-01-S2-01] EAST3 optimizer に同型 cast 縮退 pass を実装し、既存 pass 順序へ組み込む。
- [x] [ID: P0-EAST3-PYTO-IDENTITY-01-S2-02] C++ emitter 側の同型 cast 抑止を最終ガードに整理し、EAST3 pass 非適用時も fail-closed を維持する。
- [x] [ID: P0-EAST3-PYTO-IDENTITY-01-S3-01] unit / transpile check / sample 再生成で回帰を固定する。
