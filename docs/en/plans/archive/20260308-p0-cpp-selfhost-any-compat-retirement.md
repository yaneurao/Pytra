<a href="../../ja/plans/archive/20260308-p0-cpp-selfhost-any-compat-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260308-p0-cpp-selfhost-any-compat-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260308-p0-cpp-selfhost-any-compat-retirement.md`

# P0: C++ selfhost `std::any` 互換 lane の退役

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-SELFHOST-ANY-COMPAT-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [p0-cpp-pyruntime-object-lane-retirement.md](./p0-cpp-pyruntime-object-lane-retirement.md)

背景:
- `py_runtime.h` には旧 selfhost / bootstrap 互換のための `std::any` lane が残っている。
- 代表例は以下である。
  - `make_object(const ::std::any&)`
  - `py_len/py_to_string/py_to_int64/py_to_float64/py_to_bool/py_print(const ::std::any&)`
  - `py_to<T>(const ::std::any&)`
  - `str(const ::std::any&)`
  - `py_reversed(const ::std::any&)`, `py_enumerate(const ::std::any&)`
  - `std::any == ""`, `std::any > 0`, `begin/end(::std::any)` などの selfhost compat operator / iterator bridge
- checked-in repo 上で現行 production callsite はほぼ見つからず、主に runtime inventory test が「まだ残っていること」を確認しているだけである。
- ユーザー判断として後方互換性は不要になったため、旧 selfhost compat lane を permanent API として残す必要はない。

目的:
- C++ runtime から旧 selfhost `std::any` 互換 lane を削除する。
- `py_runtime.h` の high-level compat debt をさらに減らし、typed/object/JsonValue 正本へ寄せる。
- runtime inventory test を「残す」から「戻らない」に反転する。

対象:
- `src/runtime/cpp/native/core/py_runtime.h` の `::std::any` overload / helper
- `src/runtime/cpp/native/core/str.h` の `str(const ::std::any&)`
- `src/runtime/cpp/native/built_in/iter_ops.h` の `::std::any` overload
- これに伴う representative C++ runtime tests / docs / TODO

非対象:
- `object` lane の JSON accessor convenience 縮退
- `JsonValue` nominal carrier 実装
- header 分割
- backend `header_builder.py` の `<any>` include 判定削除

受け入れ基準:
- runtime checked-in source から `::std::any` compat helper が撤去される。
- `test_cpp_runtime_iterable.py` と `test_cpp_runtime_boxing.py` の inventory / smoke が新契約へ更新される。
- fixture/sample parity を維持する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `git diff --check`
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_cpp_runtime_iterable.py`
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_cpp_runtime_boxing.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

## 1. 基本方針

1. `std::any` compat は legacy selfhost support と見なし、現行 runtime surface から外す。
2. production callsite が無い helper は tests を直したうえで削除する。
3. 現行 typed/object/JsonValue lane に必要な helper まで巻き込まない。

## 2. フェーズ

### Phase 1: 棚卸し

- checked-in repo 上の `std::any` runtime helper callsite を棚卸しする。
- `compat-only` / `still-used` を分ける。

### Phase 2: core `std::any` helper 削除

- `py_runtime.h` の `make_object(any)`, `py_len(any)`, `py_to_* (any)`, `py_print(any)`, `py_slice(any)`, `py_is_* (any)` などを削除する。
- `str(const ::std::any&)` を削除する。

### Phase 3: selfhost compat operator / iter 削除

- `std::any == ""`, 数値比較、`begin/end(::std::any)` を削除する。
- `iter_ops.h` の `py_reversed/py_enumerate(any)` を削除する。

### Phase 4: regression / parity / close

- inventory guard を反転し、`std::any` lane が戻らないことを固定する。
- parity と行数差分を確認して閉じる。

## 3. タスク分解

- [ ] [ID: P0-CPP-SELFHOST-ANY-COMPAT-01] C++ runtime に残る旧 selfhost `std::any` 互換 lane を撤去する。
- [ ] [ID: P0-CPP-SELFHOST-ANY-COMPAT-01-S1-01] `std::any` runtime helper の checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-SELFHOST-ANY-COMPAT-01-S2-01] `py_runtime.h` / `str.h` の `std::any` helper を first slice で削除する。
- [ ] [ID: P0-CPP-SELFHOST-ANY-COMPAT-01-S2-02] `iter_ops.h` の `std::any` overload を削除し、tests を更新する。
- [ ] [ID: P0-CPP-SELFHOST-ANY-COMPAT-01-S3-01] `std::any` comparison / iterator compat を削除する。
- [ ] [ID: P0-CPP-SELFHOST-ANY-COMPAT-01-S3-02] regression / parity / docs を更新して閉じる。

## 4. 決定ログ

- 2026-03-08: 本計画では後方互換性を前提にしない。旧 selfhost C++ を通すためだけの `std::any` lane は撤去対象とする。
- 2026-03-08: checked-in callsite を棚卸しした結果、`std::any` lane の利用は runtime source 本体と representative runtime smoke に限られ、production codegen / sample checked-in C++ からの直接依存は見つからなかった。first slice では `py_runtime.h` / `str.h` / `iter_ops.h` の helper を削除し、inventory test を `NotIn` へ反転してよい。
- 2026-03-08: `py_runtime.h` / `str.h` / `iter_ops.h` から `std::any` helper を全面撤去した。`header_builder.py` の `<any>` include 判定は非対象のため残すが、native runtime surface には `std::any` を持ち込まない。representative runtime smoke は `object` / typed path に書き換える。
- 2026-03-08: regression と parity は `test_cpp_runtime_boxing.py`, `test_cpp_runtime_iterable.py`, `runtime_parity_check.py --targets cpp --case-root fixture`, `runtime_parity_check.py --targets cpp --case-root sample --all-samples` を通過した。C++ runtime core から `std::any` compat lane は撤去完了とする。
