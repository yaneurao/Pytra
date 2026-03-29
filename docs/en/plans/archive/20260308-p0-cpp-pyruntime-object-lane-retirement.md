<a href="../../ja/plans/archive/20260308-p0-cpp-pyruntime-object-lane-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260308-p0-cpp-pyruntime-object-lane-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260308-p0-cpp-pyruntime-object-lane-retirement.md`

# P0: C++ `py_runtime.h` object lane 退役（`dict_get_*` / object arithmetic）

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-OBJECT-LANE-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [20260308-p1-jsonvalue-decode-first-contract.md](./archive/20260308-p1-jsonvalue-decode-first-contract.md)
- [20260308-p2-jsonvalue-selfhost-decode-alignment.md](./archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md)
- [20260308-p0-cpp-pyruntime-dynamic-bridge-retirement.md](./archive/20260308-p0-cpp-pyruntime-dynamic-bridge-retirement.md)

背景:
- `P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01` で `std::any` dict access と dynamic helper 第1波は削除したが、`src/runtime/cpp/native/core/py_runtime.h` にはまだ大きい object convenience lane が残っている。
- 代表的な塊は次の 2 系統である。
  - `py_dict_get` / `py_dict_get_default` / `dict_get_*` の `object` / `optional<dict<str, object>>` convenience overload
  - `object` に対する算術演算と複合代入（`object + int`, `object - object`, `object += ...` など）
- 現在の方針では、JSON 由来の dynamic data は `JsonValue` / `JsonObj` / `JsonArr` の decode-first で扱い、`object` のまま built-in や collection helper に渡すのは compile error に寄せている。
- そのため、上記 2 系統は permanent API ではなく、旧 selfhost / 旧 runtime convenience の残りと見なせる。

目的:
- `py_runtime.h` から JSON accessor convenience と object arithmetic convenience を削減し、`JsonObj.get_*()` と typed value path を正本にする。
- `object` を「何でもできる値」として扱う surface を狭め、`py_runtime.h` の責務を low-level bridge に近づける。
- 後続の `std::any` conversion/query 縮退や `JsonValue` nominal carrier 化に向けて、user-facing convenience debt を先に落とす。

対象:
- `src/runtime/cpp/native/core/py_runtime.h` の以下
  - `py_dict_get(const object& obj, ...)`
  - `py_dict_get_maybe(const object& obj, ...)`
  - `py_dict_get_default(const object& obj, ...)`
  - `py_dict_get_default(const ::std::optional<dict<str, object>>&, ...)`
  - `dict_get_bool/str/int/float/list/node(...)`
  - `object` の算術演算子と複合代入
- これに伴う representative regression / guard / docs

非対象:
- `std::any` conversion/query（`make_object(any)`, `py_to<T>(any)`, `py_len(any)`, `py_is_*(any)` など）の撤去
- `PyObj` / `object` / `make_object` / `py_to_*` の header 分割
- `JsonValue` carrier 実装そのものの full rollout
- `match` / `cast` の言語機能設計

受け入れ基準:
- `dict_get_*` / `py_dict_get_default` の `object` / `optional<dict<str, object>>` convenience lane が大幅に縮退し、JSON decode は `JsonObj` accessor が正本になる。
- `object` に対する算術演算・複合代入が compile error 方針と矛盾しない最小 surface に縮退する。
- C++ runtime representative tests と parity が維持される。
- `py_runtime.h` の行数削減が確認できる。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_runtime_cpp_layout.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_cpp_runtime_iterable.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_cpp_runtime_boxing.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_pylib_json.py' -v`
- `python3 tools/check/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/check/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

## 1. 基本方針

1. `JsonValue` / `JsonObj` / `JsonArr` decode-first を正本にし、JSON accessor convenience を `py_runtime.h` に積み増さない。
2. `object` を具体型へ decode する前に演算する経路は compile error を正本にし、runtime convenience で救済しない。
3. `py_runtime.h` に残すのは low-level bridge と最小 compat lane のみとする。
4. convenience 削除は callsite 棚卸しと regression 追加を先に行い、false positive を避ける。

## 2. フェーズ

### Phase 1: 棚卸しと境界固定

- `dict_get_*` / `py_dict_get_default` / object arithmetic の checked-in callsite を棚卸しする。
- `JsonObj.get_*()` へ直接置換できる経路、typed dict helper に寄せられる経路、まだ compat が必要な経路を分類する。
- object arithmetic について、typed user code / selfhost / runtime test のどこに依存があるかを固定する。

### Phase 2: JSON accessor convenience 縮退

- `py_dict_get(const object&)` と `py_dict_get_default(const object&, ...)` を first slice で整理する。
- `dict_get_bool/str/int/float/list/node` の `object` / `optional<dict<str, object>>` 経路を `JsonObj` accessor か typed dict helper に置き換える。
- `optional<dict<str, object>>` lane は `JsonObj | None` / explicit decode に寄せ、不要な overload を削除する。

### Phase 3: object arithmetic 廃止

- `object + int`, `object + object`, `object -= ...` などの convenience を棚卸しし、checked-in callsite がないものから削除する。
- 残すとすれば `object == str` など decode-first 移行中の最小 compat に限る。
- 可能なら object arithmetic は全廃し、frontend/lowering 側 compile error と一致させる。

### Phase 4: guard / parity / close

- inventory guard と representative runtime smoke を更新する。
- fixture/sample parity を回し、`py_runtime.h` の行数差分を記録する。
- docs / archive / TODO 履歴を同期して閉じる。

## 3. 着手時の注意

- `src/runtime/cpp/generated/std/json.cpp` と `json.h` に未コミット差分が残っている可能性がある。今回の P0 では巻き込まない。
- `JsonObj.get_*()` はまだ first slice なので、`dict_get_*` を消す前に accessor 側の不足を必ず確認する。
- object arithmetic の削除は compile error 方針と揃えることが目的であり、単なる行数削減のために半端な compat を残さない。
- selfhost の `std::any` 比較は別 tranche で扱う。今回の主対象は `object` lane である。

## 4. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-LANE-01] `py_runtime.h` の JSON accessor convenience と object arithmetic convenience を縮退し、`JsonObj` accessor と typed value path を正本に寄せる。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-LANE-01-S1-01] `py_dict_get*` / `dict_get_*` / object arithmetic の callsite と compat 依存を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-LANE-01-S1-02] 削除順序と「残す最小 compat lane」を決定ログへ固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-LANE-01-S2-01] `py_dict_get(const object&)` / `py_dict_get_default(const object&, ...)` の first slice を削減し、`JsonObj` accessor へ寄せる。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-LANE-01-S2-02] `dict_get_bool/str/int/float/list/node` の `object` / `optional<dict<str, object>>` lane を縮退し、regression を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-LANE-01-S3-01] `object` 算術・単項演算・複合代入の callsite を棚卸しし、削除または置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-LANE-01-S3-02] object arithmetic 再侵入防止の guard / regression を追加する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-LANE-01-S4-01] representative unit / fixture / sample parity と行数差分を確認する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-LANE-01-S4-02] docs / archive / TODO 履歴を同期して本計画を閉じる。

## 5. 決定ログ

- 2026-03-08: 本計画では header 分割や `std::any` conversion/query は扱わず、`object` convenience lane の削減に集中する。
- 2026-03-08: 棚卸しの結果、checked-in の C++ callsite で残っていた `py_dict_get*` 系は `dict<str, object>` / generic dict lane のみで、`object` receiver と `optional<dict<str, object>>` receiver の convenience overload は runtime 内にしか残っていなかった。`sample/cpp/18_mini_language_interpreter.cpp` の `py_dict_get(env, node.name)` も `env: dict<str, object>` であり、`object` receiver ではない。
- 2026-03-08: `dict_get_bool/str/int/float/list/node` の checked-in codegen expectation も `dict<str, object>` lane だけで成立しており、`object` / `optional<dict<str, object>>` lane は削除対象にしてよいと決めた。`dict<str, str>` 専用の `dict_get_node` と generic `dict<K, V>` / `dict<str, V>` helper は維持する。
- 2026-03-08: `object` arithmetic (`+`, `-`, `*`, `/`, 単項 `-`, `+=`, `-=`, `*=`, `/=`) は checked-in callsite が見つからなかったため、全廃を正本とする。文字列比較 (`object == str`) と `std::nullopt` 比較は本計画の対象外として残す。
- 2026-03-08: first slice として `py_dict_get(const object&)`, `py_dict_get_maybe(const object&)`, `py_dict_get_default(const object&)`, `py_dict_get_default(optional<dict<str, object>>)` と、`dict_get_bool/str/int/float/list/node` の `object` / `optional<dict<str, object>>` lane を削除した。`dict<str, object>` と generic dict lane は維持し、C++ runtime representative tests と `test_pylib_json.py` は green を確認した。
- 2026-03-08: `object` arithmetic (`+`, `-`, `*`, `/`, 単項 `-`, `+=`, `-=`, `*=`, `/=`) を `py_runtime.h` から撤去し、inventory guard で再侵入を止めた。`rc<T>` の unary `-` と `object == str` / `object == nullopt` 比較だけは非対象として残した。
- 2026-03-08: representative verification は `test_cpp_runtime_iterable.py`, `test_cpp_runtime_boxing.py`, fixture parity `cases=3 pass=3 fail=0`, sample parity `cases=18 pass=18 fail=0` を通した。`py_runtime.h` の行数は plan 起票時基準で `2913 -> 2337` に縮退した。
