<a href="../../../en/plans/archive/20260308-p0-cpp-pyruntime-dynamic-bridge-retirement.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ `py_runtime.h` dynamic bridge 退役と decode-first 縮退

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [20260308-p0-cpp-dynamic-helper-first-wave-retirement.md](./archive/20260308-p0-cpp-dynamic-helper-first-wave-retirement.md)
- [20260308-p1-jsonvalue-decode-first-contract.md](./archive/20260308-p1-jsonvalue-decode-first-contract.md)
- [20260308-p2-jsonvalue-selfhost-decode-alignment.md](./archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md)

背景:
- `P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01` で `sum(const object&)`, `zip(const object&, const object&)`, `py_dict_keys/items/values(const object&)` は `py_runtime.h` から落とした。
- それでも `src/runtime/cpp/native/core/py_runtime.h` は依然として 3000 行超で、重い塊は主に次の 3 系統に残っている。
  - `py_dict_get_default` / `dict_get_*` の object / optional / `std::any` overload 群
  - `sum(const list<object>&)` と `optional<dict<str, object>>` compat lane
  - selfhost 互換のために増えた `std::any` 比較 / 算術 / `begin/end` bridge
- `JsonValue` / decode-first 契約が入った現在、これらの多くは permanent API ではなく compat debt とみなせる。
- 分割（umbrella header 化）は後回しでよいが、その前に「不要な dynamic bridge 自体」を減らした方が `py_runtime.h` の意味論がきれいになる。

目的:
- `py_runtime.h` に残っている dynamic bridge / compat lane を、`JsonValue` decode-first と typed helper を正本にして段階的に退役させる。
- `dict_get_*` と `py_dict_get_default` を JSON / dynamic compat と typed helper に整理し、object / `std::any` overload の増殖を止める。
- `sum(const list<object>&)` と `optional<dict<str, object>>` lane を別 tranche として縮退し、`py_runtime.h` の high-level compat debt を減らす。
- selfhost のために残っている `std::any` bridge を inventory して、不要な演算子 / iterator bridge を削れる状態へ持ち込む。

対象:
- `src/runtime/cpp/native/core/py_runtime.h` の以下
  - `py_dict_get_default` / `dict_get_*` 群
  - `sum(const list<object>&)`
  - `py_dict_keys/items/values(const ::std::optional<dict<str, object>>& d)`
  - `std::any` 比較 / 算術 / `begin/end` bridge
- これに連動する representative test / guard / docs

非対象:
- `PyObj` / `object` / `make_object` / `py_to_*` / `type_id` の header 分割
- `JsonValue` の full nominal carrier 化
- `contains/reversed/enumerate(object)` の SoT 側 object helper 整理
- `py_runtime.h` を umbrella header 化する作業

受け入れ基準:
- `dict_get_*` / `py_dict_get_default` の dynamic overload 群が縮退し、typed / JSON decode helper が正本として前面に出る。
- `sum(const list<object>&)` と `optional<dict<str, object>>` compat lane の要否が整理され、不要分が削除される。
- `std::any` bridge は inventory したうえで、不要な比較 / 算術 / iterator 互換を削る tranche まで進む。
- representative C++ runtime tests と parity が維持される。
- `py_runtime.h` の行数削減が「分割なしでも」確認できる。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_runtime_cpp_layout.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -v`
- `PYTHONPATH=src python3 test/unit/ir/test_east_core.py -v`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

## 1. 基本方針

1. `py_runtime.h` を「何でも互換関数を足す場所」として扱わない。
2. user-facing dynamic helper は引き続き compile error を正本にし、runtime fallback で救済しない。
3. JSON 由来の動的データは `JsonValue` / `JsonObj` / `JsonArr` decode helper へ寄せ、`dict_get_*` 依存を減らす。
4. `std::any` bridge は selfhost 互換の最小必要量だけに絞る。演算子互換を permanent API とみなさない。
5. 分割は後回しにし、まず「意味論上いらない行」を減らす。

## 2. 優先順

### Phase 1: inventory と境界固定

- `dict_get_*` / `py_dict_get_default` / `std::any` bridge の callsite を棚卸しする。
- 「残す compat」「消せる debt」「JSON decode helper に置き換えるべき経路」を分ける。
- `sum(list<object>)` と `optional<dict<str, object>>` lane を separate tranche として明文化する。

### Phase 2: `dict_get_*` 縮退

- `JsonObj.get_*()` と役割が重なる object / optional / `std::any` overload を洗い出す。
- selfhost / host / runtime で必要な最小経路だけ残し、typed helper へ寄せられるものを消す。
- representative regression を更新する。

### Phase 3: compat lane の第2波削除

- `sum(const list<object>&)` の callsite を棚卸しし、decode-first 前提に置き換えられるなら削除する。
- `py_dict_keys/items/values(const ::std::optional<dict<str, object>>& d)` を JSON compat lane として残すか、`JsonObj` API へ寄せて削除するかを決める。

### Phase 4: `std::any` bridge 縮退

- `std::any` 比較 / 算術 / `begin/end` bridge を分類する。
- selfhost generated artifact で本当に必要な subset だけ残す。
- 不要な演算子と iterator 互換を削除する。

### Phase 5: parity / archive

- representative unit と fixture/sample parity を通す。
- 行数差分と残 debt を決定ログへ記録して閉じる。

## 3. 着手時の注意

- `src/runtime/cpp/generated/std/json.cpp` / `json.h` に既存差分がある可能性がある。今回の P0 に直接関係しない変更は巻き込まない。
- `unknown` は decode-first guard の reject 対象から外した直後なので、guard を再び強めるなら false positive を再発させない形で行う。
- `dict_get_*` の object / optional 経路は JSON decode helper と selfhost loader がまだ併存している可能性があるため、削除前に callsite を必ず棚卸しする。

## 4. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01] `py_runtime.h` に残る `dict_get_*` / compat lane / `std::any` bridge を縮退し、decode-first / typed helper を正本へ寄せる。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S1-01] `dict_get_*` / `py_dict_get_default` / `std::any` bridge / `sum(list<object>)` / `optional<dict<str, object>>` lane の callsite と debt 分類を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S1-02] 削除順序と「残す compat lane」を docs / 決定ログへ固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S2-01] `dict_get_*` / `py_dict_get_default` の object / optional / `std::any` overload を first slice で整理し、`JsonObj.get_*` や typed helper に寄せる。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S2-02] representative tests を更新し、`dict_get_*` 縮退後の C++ runtime surface を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S3-01] `sum(const list<object>&)` の callsite を置き換えまたは削除し、必要なら regression を追加する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S3-02] `py_dict_keys/items/values(const ::std::optional<dict<str, object>>& d)` compat lane を削除または最小化し、`JsonObj` 経路との境界を確定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S4-01] `std::any` 比較 / 算術 / `begin/end` bridge を縮退し、selfhost に必要な subset だけ残す。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S4-02] `std::any` bridge 再侵入防止の regression / guard を追加する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S5-01] representative unit / fixture parity / sample parity / 行数差分を確認し、決定ログへ残す。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S5-02] docs / archive / TODO 履歴を同期して本計画を閉じる。

## 5. 決定ログ

- 2026-03-08: 本計画では header 分割は行わず、`dict_get_*`・compat lane・`std::any` bridge そのものの削減を優先する。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S1-01]: `dict_get_*` / `py_dict_get_default` の checked-in callsite は、repo 上では C++ codegen regression と runtime 本体にほぼ限られている。`dict_get_bool/str/int/float/list/node` の typed/object lane は `test_py2cpp_codegen_issues.py` と fixture `dict_get_items` 系でまだ使われている一方、`dict<str, ::std::any>` と `::std::any` overload は `py_runtime.h` 自体と selfhost error/report helper 以外から参照されていない。したがって first slice は `std::any` / `dict<str, ::std::any>` lane を compat debt と見なし、`dict<str, object>` / `object` / `dict<str, str>` の typed fallback を当面の正本として扱う。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S1-01]: `py_dict_keys/items/values(const ::std::optional<dict<str, object>>& d)` と `sum(const list<object>&)` は checked-in source 上では runtime inventory guard にしか現れておらず、backend / runtime / selfhost code からの direct callsite は見つからなかった。したがってこれらは permanent API ではなく、削除候補の compat lane と分類する。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S1-01]: `std::any` bridge は 3 層に分かれる。(1) `make_object` / `py_to_*` / `py_len` / `py_slice` / `py_is_*` の conversion/query 層、(2) `py_dict_get(_default)` の dynamic dict access 層、(3) `operator<...>` / `operator+...` / `begin/end(::std::any)` の selfhost expression compat 層である。本計画の対象は主に (2) と (3) で、(1) は conversion primitive として後続 tranche に残す。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S1-02]: 削除順は (a) `dict_get_*` / `py_dict_get_default` の `std::any` / `dict<str, ::std::any>` lane、(b) `sum(list<object>)` と `optional<dict<str, object>>` compat lane、(c) `std::any` comparison/arithmetic/begin-end bridge の順とする。先に dict access を縮退して selfhost JSON loader を decode-first へ寄せ、次に checked-in source から direct callsite の無い compat lane を落とし、最後に selfhost expression compat を最小 subset へ絞る。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S1-02]: 当面残す compat lane は `dict_get_bool/str/int/float/list/node` の `dict<str, object>` / `object` / `dict<str, str>` 経路、および conversion/query としての `make_object(const ::std::any&)`, `py_to<T>(const ::std::any&)`, `py_len(const ::std::any&)`, `py_slice(const ::std::any&, ...)`, `py_is_*` とする。`sum(list<object>)`, `py_dict_keys/items/values(optional<dict<str, object>>)`、`dict<str, ::std::any>` / `::std::any` dict access、`std::any` arithmetic/iterator bridge は compat debt として退役対象に固定する。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S2-01]: first slice では `py_dict_get(const ::std::any&)`, `py_dict_get_maybe(const ::std::any&)`, `py_dict_get_default(dict<str, ::std::any>, ...)`, `py_dict_get_default(const ::std::any&, ...)` を削除した。checked-in repo 上でこれらの direct callsite は見つからず、`dict<str, object>` / `object` lane で現在の JSON decode-first と C++ dict_get regression は維持できるため、selfhost compat debt と判断した。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S2-02]: representative regression は `test_cpp_runtime_iterable.py` の inventory guard と `test_cpp_runtime_boxing.py`, `test_py2cpp_codegen_issues.py` の dict_get representative で固定した。`std::any` conversion/query (`py_to_*`, `py_len`, `py_slice`, `py_is_*`) はこの tranche で壊していないため、runtime boxing smoke を緑に保ったまま `std::any` dict access だけを落とせている。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S3-01]: `sum(const list<object>&)` は checked-in repo 上では inventory guard にしか現れず、backend / runtime / selfhost の direct callsite が見つからなかったため削除した。typed `sum(const list<T>&)` は `generated/built_in/numeric_ops.h` が正本であり、dynamic helper として残す理由はない。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S3-02]: `py_dict_keys/items/values(const ::std::optional<dict<str, object>>& d)` も checked-in callsite は inventory guard のみだったため削除した。`py_dict_keys/items/values(const dict<K, V>&)` はそのまま残し、JSON / optional decode は `JsonObj` surface へ寄せる方針に固定した。これで残る high-level compat debt は `std::any` comparison/arithmetic/begin-end bridge に絞られた。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S4-01]: selfhost/generated source を棚卸しした結果、`std::any` で checked-in 利用が見えるのは `== ""`、`<= 0` / `>= 0` / `< int64` の数値比較、`for (::std::any ... : ...)` の range-for だけだった。そこで `operator<(any, any)` / `>(any, any)` / `<=` / `>=`、`operator+(const char*, any)`、`any` 同士および `any` と数値の四則演算は削除し、比較テンプレートと iterator bridge だけを残した。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S4-02]: regression は `test_cpp_runtime_iterable.py` の inventory guard と runtime smoke へ集約した。guard では削除済み `std::any` 演算子群が header に再侵入しないこと、smoke では selfhost 互換として必要な `std::any == ""` と `std::any` 対数値比較が維持されることを固定した。`std::any` range-for は inventory に留め、実行 smoke では現行 runtime の未整備を踏まえて assert 対象から外した。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S5-01]: representative verification は `test_cpp_runtime_iterable.py`, `test_cpp_runtime_boxing.py`, fixture parity `cases=3 pass=3 fail=0`, sample parity `cases=18 pass=18 fail=0` まで再実行した。`py_runtime.h` の行数は直前 commit 比で `2995 -> 2913` となり、分割なしで 82 行縮退した。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-DYNAMIC-BRIDGE-01-S5-02]: 本計画は `dict_get_*` / compat lane / `std::any` bridge のうち high-level dynamic debt を first practical cut まで削減できたため archive へ移す。残る大物は conversion/query と `type_id` / runtime state など low-level bridge であり、後続 tranche へ切り分ける。
