# P0: C++ `py_enumerate_list_as<T>()` 導入（`py_to_str_list_from_object` 中間コピー撤去）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-ENUM-LIST-AS-01`

背景:
- `cpp_list_model=pyobj` で `enumerate(lines)`（`lines: list[str]`）を typed loop に戻す際、現行は `py_enumerate(py_to_str_list_from_object(lines))` を出力している。
- `py_to_str_list_from_object()` は `object` 内の list 要素を `obj_to_str` で再走査し、新しい `list<str>` を構築するため、不要な中間コピーが発生する。
- sample/18 の tokenize ループはこの経路を通るため、hot path の無駄になっている。

目的:
- runtime に `py_enumerate_list_as<T>(const object&)`（+ `start` オーバーロード）を追加し、`object(list<object>)` を直接列挙して `list<tuple<int64, T>>` を返す fastpath を導入する。
- C++ emitter の typed enumerate 復元経路を `py_to_str_list_from_object(...)` から `py_enumerate_list_as<str>(...)` へ置換し、中間 `list<str>` 構築を除去する。

対象:
- `src/runtime/cpp/pytra-core/built_in/py_runtime.h`（`py_enumerate_list_as<T>` 追加）
- `src/hooks/cpp/emitter/stmt.py`（typed enumerate fastpath 出力変更）
- `test/unit/test_py2cpp_codegen_issues.py`（sample/18 固定文字列の更新）
- 必要に応じて `test/unit/test_cpp_runtime_boxing.py` 等 runtime 回帰

非対象:
- `py_enumerate(object)` 既存 API 契約変更
- `str`/`dict`/`set` 向け汎用 `py_enumerate_as<T>` の導入
- `cpp_list_model=value` 経路の変更

受け入れ基準:
- `sample/18` の `cpp_list_model=pyobj` 出力で `py_enumerate(py_to_str_list_from_object(lines))` が消え、`py_enumerate_list_as<str>(lines)` を用いる。
- `py_enumerate_list_as<str>(..., start)` を含む start 指定経路も正しく出力・動作する。
- `check_py2cpp_transpile` と関連 unit が通る。
- 既存の fail-closed（非 list/object 不一致時の安全側挙動）を維持する。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`

決定ログ:
- 2026-03-01: ユーザー指示により、`py_to_str_list_from_object` による中間 list 構築を避けるため、`py_enumerate_list_as<T>()` を導入する P0 タスクを起票した。
- 2026-03-01: API 名は list 専用であることを明示するため `py_enumerate_list_as<T>` を採用し、汎用 `py_enumerate_as<T>` は非対象とした。

## 分解

- [ ] [ID: P0-CPP-ENUM-LIST-AS-01-S1-01] runtime に `py_enumerate_list_as<T>(object[, start])` を追加し、`object(list<object>)` から typed tuple 列挙を生成する。
- [ ] [ID: P0-CPP-ENUM-LIST-AS-01-S2-01] `stmt.py` の typed enumerate fastpath を `py_enumerate_list_as<str>(...)` 出力へ切替える。
- [ ] [ID: P0-CPP-ENUM-LIST-AS-01-S2-02] sample/18 回帰テストの期待値を更新し、`py_to_str_list_from_object` 非依存を固定する。
- [ ] [ID: P0-CPP-ENUM-LIST-AS-01-S3-01] unit/transpile/sample 再生成を実行し、非退行を確認する。
