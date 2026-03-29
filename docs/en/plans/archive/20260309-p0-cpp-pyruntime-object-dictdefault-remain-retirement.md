<a href="../../ja/plans/archive/20260309-p0-cpp-pyruntime-object-dictdefault-remain-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-object-dictdefault-remain-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-object-dictdefault-remain-retirement.md`

# P0: C++ `py_runtime.h` 残存 `dict<str, object>` default lane 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [archive/20260308-p1-jsonvalue-decode-first-contract.md](./archive/20260308-p1-jsonvalue-decode-first-contract.md)
- [archive/20260308-p0-cpp-pyruntime-object-dict-default-retirement.md](./archive/20260308-p0-cpp-pyruntime-object-dict-default-retirement.md)

背景:
- [py_runtime.h](../../src/runtime/cpp/native/core/py_runtime.h) にはまだ `dict<str, object>` に対する generic default getter が残っている。
- 現在残っているのは `template <class D> py_dict_get_default(const dict<str, object>&, const char*|str|string, const D&)` の 3 本であり、`object` / `str` / scalar / nominal type への fallback cast をまとめて吸っている。
- これは以前の object-dict convenience tranche で plain overload を減らした後に残した最小互換だが、`JsonObj.get_*()` と explicit decode-first が整った現在では、さらに狭める余地がある。
- とくに compiler/backend 側の codegen がこの helper を安易に使い続けると、`object` 境界が `JsonObj` へ寄らず、`py_runtime.h` の縮小が止まる。

目的:
- `dict<str, object>` 専用の generic default lane を棚卸しし、不要な checked-in callsite を explicit `find/contains + py_to<T>` か `JsonObj.get_*()` に移す。
- 最終的に `py_runtime.h` に残す必要があるなら最小 subset へ縮退し、不要なら helper 自体を削除する。

対象:
- `src/runtime/cpp/native/core/py_runtime.h` の `py_dict_get_default(const dict<str, object>&, ...)`
- C++ emitter / generated runtime / checked-in sample の代表 callsite

非対象:
- `dict<K, V>` 一般の typed `py_dict_get_default`
- `JsonObj` API 自体の新規拡張
- `dict<str, str>` 専用 helper（別タスク）

受け入れ基準:
- `dict<str, object>` 専用 generic default helper の checked-in callsite が棚卸しされている。
- 代表 callsite が explicit decode-first へ移行し、不要な helper lane を削除または最小化できている。
- representative C++ runtime/codegen test と parity が green である。

確認コマンド:
- `PYTHONPATH=src python3 tools/unittest/emit/cpp/test_cpp_runtime_iterable.py`
- `PYTHONPATH=src python3 tools/unittest/emit/cpp/test_py2cpp_codegen_issues.py`
- `PYTHONPATH=src python3 tools/unittest/emit/cpp/test_pylib_json.py`
- `python3 tools/check/runtime_parity_check.py --targets cpp --case-root fixture`

## フェーズ

### Phase 1: callsite 棚卸し

- checked-in code で `py_dict_get_default(dict<str, object>, ...)` を使っている箇所を `rg` で特定する。
- `JsonObj.get_*()` に寄せられるものと、emitter 側の typed decode へ落とすべきものを分類する。

### Phase 2: representative 置換

- C++ emitter または generated runtime の代表 callsite を explicit `contains/find -> py_to<T>` へ置き換える。
- `JsonObj.get_*()` へ置換できる箇所は helper 呼び出しをやめる。

### Phase 3: helper 縮退と固定

- `py_runtime.h` から不要な overload を削除するか、残す最小 subset だけに縮める。
- representative test / parity / docs を更新し、archive へ移す。

## タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01] 残存 `dict<str, object>` default lane を退役または最小化する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S1-01] `py_dict_get_default(dict<str, object>, ...)` の checked-in callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S1-02] `JsonObj.get_*()` / explicit decode への置換方針を固定する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S2-01] representative callsite を置換する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S2-02] helper lane を削除または最小化する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S3-01] representative test / parity を更新する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S3-02] docs / archive を同期して閉じる。

## 決定ログ

- 2026-03-09: 起票時点で残っている `dict<str, object>` default lane は `template <class D>` の 3 overload のみで、plain object-dict default overload tranche とは別件とする。今回はこの generic fallback を対象にし、`dict<K, V>` 一般の typed default helper は非対象に固定する。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S1-01]: checked-in callsite は `src/runtime/cpp/native/compiler/backend_registry_static.cpp` の `target_lang` decode と、C++ emitter の `dict[str, object].get(key, default)` lowering に集約されていた。generated JSON runtime には helper の直接 callsite はなく、main debt は emitter shortcut だと確定した。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S1-02]: helper 除去後も semantics を変えないため、`str` は `py_to_string(...)` を維持し、それ以外の scalar / nominal type は `py_object_try_cast<T>(...)` で soft-fallback させる方針に固定した。`list[...]` だけは既存の `py_to<list<T>>` lane を維持する。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S2-01]: `CppEmitter._render_objectish_dict_get_default_expr()` の non-optional object-dict shortcut を削除し、すべて explicit `find + decode` lambda に統一した。`src/runtime/cpp/native/compiler/backend_registry_static.cpp` の `target_lang` 読み出しも `find + py_to_string` に置換した。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S2-02]: `src/runtime/cpp/native/core/py_runtime.h` から `template <class D> py_dict_get_default(const dict<str, object>&, const char*|str|string, const D&)` の 3 overload を削除した。`test_cpp_runtime_iterable.py` に template signature の inventory guard を追加した。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S3-01]: verification は targeted `test_py2cpp_codegen_issues` 7件、`test_cpp_runtime_iterable.py`、`test_pylib_json.py`、fixture parity `cases=3 pass=3 fail=0` を通した。full `test_py2cpp_codegen_issues.py` には `save_gif` keyword-order の既存別件 failure があるため、本 tranche では targeted suite を正本 gate にした。
