# P0: C++ `py_runtime.h` `object == str` 比較 lane 退役

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01`

関連:
- [spec-dev.md](../spec/spec-dev.md)

背景:
- `object == char*`, `char* == object`, `object == str`, `str == object` とその `!=` がまだ残っている。
- decode-first 方針では、比較前に concrete type へ寄せるべきであり、runtime convenience は不要になりやすい。

目的:
- object-string comparison convenience を退役し、typed comparison を正本にする。

非対象:
- `object == nullopt` の None 判定 compat
- typed `str == str`

受け入れ基準:
- object-string comparison overload が削除または最小化される。
- checked-in code が explicit decode / typed comparison で通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -v`

## 1. 方針

1. object-string 比較 callsite を棚卸しする。
2. `JsonValue.as_str()` / typed decode へ寄せる。
3. `nullopt` 比較 compat は別扱いにする。

## 2. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01] object-string comparison convenience を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S1-01] object-string 比較 callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S1-02] explicit decode 置換方針を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S2-02] comparison overload を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S3-01] guard / parity / docs を更新する。

## 3. 決定ログ

- 2026-03-08: object-string convenience は decode-first 方針と逆向きなので、`nullopt` 比較と切り分けて退役する。
