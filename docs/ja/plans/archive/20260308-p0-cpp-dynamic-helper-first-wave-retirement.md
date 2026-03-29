<a href="../../../en/plans/archive/20260308-p0-cpp-dynamic-helper-first-wave-retirement.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ `py_runtime.h` dynamic helper 第1波退役

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [20260308-p1-jsonvalue-decode-first-contract.md](./archive/20260308-p1-jsonvalue-decode-first-contract.md)
- [20260308-p2-jsonvalue-selfhost-decode-alignment.md](./archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md)

背景:
- `JsonValue` decode-first 契約と selfhost 側の JSON decode helper への移行により、`object` 値を built-in / collection helper に直接渡さない前提は docs と representative path の両方で固まった。
- それにもかかわらず `src/runtime/cpp/native/core/py_runtime.h` には、過去の dynamic fallback として `sum(const object&)`, `zip(const object&, const object&)`, `py_dict_keys/items/values(const object&)` が残っている。
- これらは現在の target design では permanent API ではなく、`py_runtime.h` 縮退の邪魔になっている。
- 既に frontend 側では `sum/zip/sorted/min/max` と `keys/items/values` の dynamic receiver / argument を compile error に寄せる guard が入っているため、この tranche では C++ runtime から object overload を撤去できるはずである。

目的:
- `py_runtime.h` に残っている user-facing dynamic helper fallback のうち、最小で安全に落とせる object overload 群を第1波として撤去する。
- compile error guard と runtime surface を一致させ、`object` built-in fallback を再侵入させにくくする。
- `py_runtime.h` の縮退を small safe steps で進める。

対象:
- `src/runtime/cpp/native/core/py_runtime.h` の以下の object overload
  - `sum(const object&)`
  - `zip(const object&, const object&)`
  - `py_dict_keys(const object&)`
  - `py_dict_items(const object&)`
  - `py_dict_values(const object&)`
- 上記削除に伴う representative test / docs / guard 更新

非対象:
- `sum(const list<object>&)` の撤去
- `py_dict_keys/items/values(const ::std::optional<dict<str, object>>& d)` の撤去
- `contains/reversed/enumerate(object)` など SoT 側 object helper の整理
- `make_object`, `py_to_*`, `type_id`, `std::any` bridge のような low-level runtime の分割
- `py_runtime.h` 全体の umbrella header 化

受け入れ基準:
- `py_runtime.h` から上記 5 個の object overload が削除される。
- frontend/lowering の compile error 契約と C++ runtime surface が矛盾しない。
- C++ representative tests と runtime parity が維持される。
- 再侵入防止の guard / regression が追加される。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_runtime_cpp_layout.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_cpp_runtime_iterable.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -v`
- `python3 tools/check/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/check/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

## 1. 基本方針

1. object overload は「今も使われている convenience API」ではなく、「compile error 導入前の fallback debt」とみなす。
2. 第1波は object overload のみを削り、`list<object>` や `optional<dict<str, object>>` は別 tranche に残す。
3. 既存 emitter / frontend が typed receiver を `py_dict_keys/items/values(d)` と出している経路はそのまま維持し、overload resolution で typed path だけが残る形にする。
4. user-facing dynamic helper が再侵入しないよう、test と guard を同時に締める。

## 2. 削除対象

削除対象:

- `static inline object sum(const object& values)`
- `static inline list<::std::tuple<object, object>> zip(const object& lhs, const object& rhs)`
- `static inline list<str> py_dict_keys(const object& obj)`
- `static inline list<object> py_dict_items(const object& obj)`
- `static inline list<object> py_dict_values(const object& obj)`

第1波で残すもの:

- `sum(const list<object>& values)`
- `py_dict_keys/items/values(const ::std::optional<dict<str, object>>& d)`
- `dict_get_*` / `py_dict_get_default`

理由:
- 第1波は「compile error で既に禁止した surface」と 1 対 1 に対応する削除だけを行う。
- `optional<dict<str, object>>` や `list<object>` は JSON / decode helper の compat lane と still-internal dynamic bridge に近く、ここで一緒に触ると tranche が広がりすぎる。

## 3. 実装方針

### Phase 1: inventory と契約再確認

- `py_runtime.h` object overload の callsite を棚卸しする。
- representative test のうち「今は残っていること」を確認している assertion を「無いこと」へ反転する。
- `spec-runtime` / `spec-dev` の現契約で今回の tranche が正当化されることを確認する。

### Phase 2: object overload 撤去

- `sum(const object&)` と `zip(const object&, const object&)` を削除する。
- `py_dict_keys/items/values(const object&)` を削除する。
- typed overload と `optional<dict<str, object>>` overload は温存し、C++ emitter の typed path を壊さない。

### Phase 3: guard / parity 固定

- `test_cpp_runtime_iterable.py` などの inventory guard を更新する。
- 必要なら `check_runtime_cpp_layout.py` か専用 regression に「object dynamic helper が戻ったら fail」を追加する。
- fixture/sample parity を通し、archive まで閉じる。

## 4. タスク分解

- [ ] [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01] `py_runtime.h` の object dynamic helper 第1波を撤去し、compile error 契約と runtime surface を一致させる。
- [ ] [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01-S1-01] object overload の callsite / guard / representative test を棚卸しし、第1波の削除対象を固定する。
- [ ] [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01-S1-02] docs / 決定ログに「第1波は object overload のみ、`list<object>` と `optional<dict<str, object>>` は別 tranche」と明記する。
- [ ] [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01-S2-01] `sum(const object&)` と `zip(const object&, const object&)` を `py_runtime.h` から削除し、representative test を更新する。
- [ ] [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01-S2-02] `py_dict_keys/items/values(const object&)` を `py_runtime.h` から削除し、typed emitter path と regression を更新する。
- [ ] [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01-S3-01] object dynamic helper の再侵入防止 guard / inventory test を追加または強化する。
- [ ] [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01-S3-02] C++ representative test / fixture parity / sample parity / docs archive を完了し、本計画を閉じる。

## 5. 決定ログ

- 2026-03-08: 第1波は `py_runtime.h` の object overload 5 件だけを削除対象とする。`list<object>` と `optional<dict<str, object>>` は同時に触らない。
- 2026-03-08 [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01-S1-01]: `py_runtime.h` object overload 5 件の repo 内参照を棚卸しした結果、実 callsite は runtime header 自身だけで、外部からの直接利用は representative inventory test に限られることを確認した。`test_cpp_runtime_iterable.py` は現在これらの signature が「存在すること」を確認しており、S2 以降ではこの assertion を「存在しないこと」へ反転すればよい。
- 2026-03-08 [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01-S1-01]: `test_east_core.py` と `test_py2cpp_features.py` には `sum()` / `zip()` に `object/unknown` を渡すと compile error になる regression が既に入っている。したがって第1波の runtime 削除は frontend 契約と整合する。
- 2026-03-08 [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01-S1-02]: 第1波の削除範囲は docs 上も object overload 5 件だけに固定し、`sum(const list<object>&)` と `py_dict_keys/items/values(const ::std::optional<dict<str, object>>& d)` は JSON/decode compat lane のため別 tranche に残す。`contains/reversed/enumerate(object)` も本計画の対象外とする。
- 2026-03-08 [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01-S2-01]: `sum(const object&)` と `zip(const object&, const object&)` を `py_runtime.h` から削除した。runtime smoke の `zip` representative case は `object` のまま helper を呼ぶのではなく `py_to<list<object>>(...)` で decode してから typed `zip` を使う形へ更新し、decode-first 契約と runtime surface を一致させた。
- 2026-03-08 [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01-S2-02]: `py_dict_keys/items/values(const object&)` を `py_runtime.h` から削除した。typed overload と `optional<dict<str, object>>` overload は温存し、既存 emitter の `py_dict_keys(d)` / `py_dict_values(d)` 出力はそのまま typed path に解決される。
- 2026-03-08 [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01-S3-01]: `test_cpp_runtime_iterable.py` の inventory guard を反転し、削除した object overload 5 件が再侵入したら fail、`sum(const list<object>&)` と `optional<dict<str, object>>` overload はまだ残ることを同時に固定した。第1波と後続 tranche の境界を regression で表現する。
- 2026-03-08 [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01-S3-02]: `unknown` を decode-first guard の禁止対象から外し、dynamic helper reject を `object/Any` のみに絞った。`unknown` は型推論不足でも現れうるため、この tranche では false positive を避ける方を優先した。
- 2026-03-08 [ID: P0-CPP-DYNAMIC-HELPER-FIRSTWAVE-01-S3-02]: representative verification として `test_cpp_runtime_iterable.py`, `test_py2cpp_features.py -k json`, `check_runtime_cpp_layout.py`, fixture parity `cases=3 pass=3 fail=0` を再実行した。sample parity は一度 `14_raymarching_light_cycle` / `16_glass_sculpture_chaos` が `unknown` guard で落ちたため、guard 緩和後にこの 2 case を再実行して `pass=2 fail=0` を確認し、直前の `16/18` green と合わせて full sample lane の非退行を判断した。
