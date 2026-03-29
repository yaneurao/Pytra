<a href="../../ja/plans/archive/20260308-p0-cpp-pyruntime-object-string-compare-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260308-p0-cpp-pyruntime-object-string-compare-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260308-p0-cpp-pyruntime-object-string-compare-retirement.md`

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
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_cpp_runtime_iterable.py' -v`

## 1. 方針

1. object-string 比較 callsite を棚卸しする。
2. `JsonValue.as_str()` / typed decode へ寄せる。
3. `nullopt` 比較 compat は別扱いにする。

## 2. タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01] object-string comparison convenience を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S1-01] object-string 比較 callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S1-02] explicit decode 置換方針を固定する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S2-01] representative callsite を置換する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S2-02] comparison overload を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S3-01] guard / parity / docs を更新する。

## 3. 決定ログ

- 2026-03-08: object-string convenience は decode-first 方針と逆向きなので、`nullopt` 比較と切り分けて退役する。
- 2026-03-08: checked-in C++ backend/runtime/sample を棚卸しした結果、`object == str` / `object == char*` の明示 callsite は残っていなかった。`test_cpp_runtime_iterable.py` の inventory guard を正本にし、runtime overload 自体を削除して非退行を確認した。
