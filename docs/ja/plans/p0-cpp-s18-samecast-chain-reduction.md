# P0: sample/18 C++ 同型 cast 連鎖の追加削減

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S18-SAMECAST-02`

背景:
- `sample/cpp/18_mini_language_interpreter.cpp` には `int64(py_to<int64>(...))` のような同型 cast 連鎖が残っている。
- 既存の同型 cast 縮退は一部経路（`str -> str` 等）に限定され、dict 取得や補助関数戻り値経路で冗長 cast が再混入している。
- 可読性低下に加え、実行時オーバーヘッドと inlining 妨げの原因になる。

目的:
- `sample/18` で観測される同型 cast 連鎖を削減し、型既知経路では直接値を利用する出力へ寄せる。

対象:
- EAST3 側 cast メタ/`NoOpCast` 縮退条件の拡張
- C++ emitter の `py_to<T>` / `static_cast<T>` 出力条件見直し
- `sample/18` の回帰テスト（冗長 cast 非出力）

非対象:
- 型変換が必要な境界（`object` unbox、整数/浮動小数点変換）の削除
- C++ 以外 backend の cast 規則変更

受け入れ基準:
- `sample/cpp/18_mini_language_interpreter.cpp` に `int64(py_to<int64>(...))` が残らない。
- 型未確定経路では従来どおり fail-closed で安全側キャストを維持する。
- `test_py2cpp_codegen_issues.py` / `check_py2cpp_transpile.py` が通過する。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --stems 18_mini_language_interpreter --force --verbose`

決定ログ:
- 2026-03-01: ユーザー指示により、sample/18 の同型 cast 連鎖削減を `P0` で起票した。

## 分解

- [ ] [ID: P0-CPP-S18-SAMECAST-02-S1-01] sample/18 の冗長 cast 発生点（dict取得/補助関数戻り値）を棚卸しし、削減対象を固定する。
- [ ] [ID: P0-CPP-S18-SAMECAST-02-S2-01] EAST3 cast cleanup / C++ emitter 条件を更新し、同型 cast 連鎖を縮退する。
- [ ] [ID: P0-CPP-S18-SAMECAST-02-S2-02] 回帰テストを追加し、`int64(py_to<int64>(...))` 再発を検知できるようにする。
- [ ] [ID: P0-CPP-S18-SAMECAST-02-S3-01] sample/18 を再生成し、コード差分と transpile 回帰で非退行を確認する。
