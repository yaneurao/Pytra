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
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_cpp_runtime_iterable.py`
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_py2cpp_codegen_issues.py`
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_pylib_json.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`

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

- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01] 残存 `dict<str, object>` default lane を退役または最小化する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S1-01] `py_dict_get_default(dict<str, object>, ...)` の checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S1-02] `JsonObj.get_*()` / explicit decode への置換方針を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S2-02] helper lane を削除または最小化する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S3-01] representative test / parity を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTDEFAULT-REMAIN-01-S3-02] docs / archive を同期して閉じる。

## 決定ログ

- 2026-03-09: 起票時点で残っている `dict<str, object>` default lane は `template <class D>` の 3 overload のみで、plain object-dict default overload tranche とは別件とする。今回はこの generic fallback を対象にし、`dict<K, V>` 一般の typed default helper は非対象に固定する。
