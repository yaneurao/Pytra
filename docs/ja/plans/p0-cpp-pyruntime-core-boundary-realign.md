# P0: C++ `py_runtime.h` の core 境界を再整理し、残存 helper を上流 / 専用lane へ戻す

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01`

関連:
- `docs/ja/spec/spec-runtime.md`
- `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-upstream-realign.md`
- `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-process-surface-realign.md`
- `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-scope-exit-lane-realign.md`

背景:
- `src/runtime/cpp/native/core/py_runtime.h` は `print/ord/chr/int(x, base)`、process surface、scope_exit などの first wave を既に退役済みだが、なお `core` に残す理由が薄い helper が残っている。
- 現在の主な残件は、`generated/built_in` companion の再集約、typed convenience helper、tuple 取得 helper、`type_id` 手書き wrapper である。
- `docs/ja/spec/spec-runtime.md` は `native/core/py_runtime.h` に high-level built_in semantics を permanent に残さないこと、`string_ops` 以外の built_in companion を transitive include で再流入させないことを要求している。
- しかし現状は `py_runtime.h` が `runtime/cpp/generated/built_in/numeric_ops.h` と `runtime/cpp/generated/built_in/zip_ops.h` を直 include し、`contains` も `native/core` から抱えている。これは emitter 側の include 収集不足を `core` が肩代わりしている状態である。
- また `py_dict_get` や tuple `py_at`、typed list mutation helper 群の一部は、runtime ABI というより C++ backend の lowering 都合で残っている。こうした helper を `core` に置いたままにすると、他 target runtime でも同種の surface を誤って増やしやすい。
- `type_id` については generated SoT が存在する一方、`py_runtime.h` 側に `py_register_class_type` / `py_is_subtype` / `py_runtime_type_id` / `py_isinstance` が残り、generated `type_id.cpp` がそれらを逆参照して ownership が循環している。

目的:
- `src/runtime/cpp/native/core/py_runtime.h` に残す責務を、`PyObj` / `object` / `rc<>` / raw `type_id` primitive / low-level container primitive / dynamic iteration / 算術 primitive に寄せる。
- `core` が high-level built_in include collector や backend compat layer になっている箇所を解消する。
- `type_id` 判定の ownership を generated SoT 主体へ寄せ、手書き wrapper を最小化する。
- 今後の他 target runtime 実装時に、C++ core 由来の不要 helper を横展開しない状態へ戻す。

対象:
- `src/runtime/cpp/native/core/py_runtime.h`
- `src/runtime/cpp/core/py_runtime.h`
- `src/runtime/cpp/generated/built_in/type_id.*`
- `src/runtime/cpp/generated/built_in/numeric_ops.h`
- `src/runtime/cpp/generated/built_in/zip_ops.h`
- `src/runtime/cpp/native/built_in/contains.h`
- `src/backends/cpp/emitter/module.py`
- `src/backends/cpp/emitter/runtime_expr.py`
- `src/backends/cpp/emitter/cpp_emitter.py`
- 必要に応じて `src/backends/cpp/emitter/stmt.py` / `collection_expr.py`
- 関連 test / spec / TODO

非対象:
- `PyObj` / `object` / boxing / unboxing の全面再設計
- dynamic iteration primitive の全面撤去
- `py_div` / `py_floordiv` / `py_mod` の移設
- `docs/en/` の同時同期
- 「header を別 header に分割して行数だけ減らす」対応

受け入れ基準:
- `py_runtime.h` から `numeric_ops` / `zip_ops` / `contains` の暗黙 include 依存が外れ、必要 caller が explicit include する。
- typed dict subscript の checked-in path が `py_dict_get` 依存をやめ、`py_runtime.h` から `py_dict_get` を削除できる。
- tuple constant-index の generated/runtime path が `std::get<N>` へ寄り、tuple `py_at` helper を `core` から外すか、少なくとも checked-in caller を失わせる。
- `type_id` の registry / subtype / isinstance ownership が `py_tid_*` 主体に寄り、`py_runtime.h` の手書き実装は薄い delegate か raw primitive に縮小される。
- `py_isinstance_of` fast path や `PyFile` alias のような redundant surface を棚卸しし、残す理由が無いものは削除する。
- representative C++ backend/runtime test と parity が非退行で通る。
- `python3 tools/check_todo_priority.py` が通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_type_id.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k json`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k argparse_extended_runtime`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `git diff --check`

## 優先順位

本件は次の順で進める。`type_id` だけを先に触ると回帰面が広く、逆に include ownership を先に正すと surface 削減と test 追加がしやすい。

1. `numeric_ops/zip_ops/contains` の explicit include 化
2. `py_dict_get` と tuple `py_at` の upstream 化
3. typed list/dict mutation helper の object bridge 専用化
4. `type_id` ownership の反転
5. small cleanup と docs/archive

## 現時点の分類

### A. `core` から追い出すべき include / companion

- `runtime/cpp/generated/built_in/numeric_ops.h`
- `runtime/cpp/generated/built_in/zip_ops.h`
- `runtime/cpp/native/built_in/contains.h`

理由:
- `spec-runtime` の `py_runtime` contract に反する。
- `module.py` の helper include collector が `zip` / `contains` / numeric helper を拾えていないだけで、`core` に permanent に残す理由は無い。
- `numeric_ops.h` / `zip_ops.h` 自身が `runtime/cpp/core/py_runtime.h` を include しており、責務境界が循環している。

### B. upstream 化候補

- typed dict subscript から呼ばれる `py_dict_get`
- tuple `py_at(const ::std::tuple<...>&, int64)`
- typed `append/extend/pop/clear/reverse/sort/set_at`

理由:
- typed lane では backend が直接 `std::get` / `.at()` / member call / primitive helper に落とせる。
- `core` に generic convenience として残すと、ABI 面より emitter 都合が優先されてしまう。

### C. ownership を薄くすべき `type_id`

- `py_register_class_type`
- `py_is_subtype`
- `py_issubclass`
- `py_runtime_type_id`
- `py_isinstance`

理由:
- generated `type_id.cpp` に SoT があるのに、`core` の手書き wrapper を逆参照している。
- `core` に残すべきなのは `PYTRA_TID_*` 定数、`PYTRA_DECLARE_CLASS_TYPE`、`PyObj` が返す raw tag 取得程度である。

### D. small cleanup 候補

- `value->py_isinstance_of(expected_type_id)` fast path
- `using PyFile = pytra::runtime::cpp::base::PyFile`

理由:
- checked-in override / caller が見当たらず、surface を減らしても意味を保ちやすい。

## フェーズ

### Phase 1: 棚卸しと contract 固定

1. `py_runtime.h` 内の対象 helper を `explicit include / upstream / object bridge only / keep` に分類する。
2. checked-in caller を `src/backends/cpp`, `src/runtime/cpp/generated`, test, sample で洗う。
3. `spec-runtime` の current contract と矛盾しない end state を決定ログに固定する。

### Phase 2: include ownership の是正

1. `module.py` の helper include collector が `zip` / `contains` / numeric helper を拾えるようにする。
2. 生成物や prelude で必要な include を explicit に出す。
3. `py_runtime.h` から `numeric_ops` / `zip_ops` / `contains` の transitive include を削除する。
4. `check_runtime_cpp_layout.py` 相当の guard や unit test に removed include inventory を追加する。

### Phase 3: typed convenience helper の upstream 化

1. typed dict subscript を `.at()` へ寄せ、`py_dict_get` の remaining callsite を消す。
2. tuple constant-index の runtime/generated path を `std::get<N>` へ揃える。
3. typed `append/extend/pop/clear/reverse/sort/set_at` の direct lowering を増やし、runtime helper を object bridge 専用 surface まで縮める。
4. 「typed lane を増やすために新しい generic core helper を足す」ことは禁止する。

### Phase 4: `type_id` ownership の反転

1. `py_tid_runtime_type_id` / `py_tid_is_subtype` / `py_tid_isinstance` を canonical entrypoint として扱う。
2. `py_runtime.h` の `py_is_subtype` / `py_runtime_type_id` / `py_isinstance` は thin delegate に縮めるか、checked-in caller を `py_tid_*` へ直接寄せる。
3. `py_register_class_type` と `PYTRA_DECLARE_CLASS_TYPE` の扱いを整理し、user type registry の ownership をどこに置くか決める。
4. `test_cpp_runtime_type_id.py` と generated runtime callsite で non-regression を固定する。

### Phase 5: cleanup / docs / archive

1. `py_isinstance_of` fast path と `PyFile` alias のような small cleanup を片付ける。
2. inventory guard / docs / TODO / archive を同期する。
3. `check_todo_priority.py` と representative verification を通して閉じる。

## 実装ルール

- `py_runtime.h` から削るために temporary compat alias を新設しない。
- include 不足を `core` 側の再集約で隠さない。
- `type_id` の手書き helper を残す場合も、generated SoT を逆参照させるのではなく、generated 側を正本にする。
- `py_dict_get` を削る際は object dict / optional dict の旧 tranche を再導入しない。
- 途中で未コミット差分が増えた場合も、本 `ID` の範囲内で完結するまで別 ID を混ぜない。

## タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01] `py_runtime.h` の core 境界を再整理し、残存 helper を上流 / 専用lane へ戻す。
- [x] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S1-01] `numeric_ops/zip_ops/contains`、typed helper、tuple helper、`type_id` wrapper の checked-in caller を棚卸しし、end state を分類する。
- [x] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S1-02] `spec-runtime` に反しない include ownership / upstream contract / non-goal を決定ログへ固定する。
- [x] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S2-01] C++ emitter / prelude / generated path の helper include 収集を拡張し、`zip` / `contains` / numeric helper を explicit include 化する。
- [x] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S2-02] `py_runtime.h` から `numeric_ops` / `zip_ops` / `contains` の transitive include を削除し、removed-include guard を更新する。
- [x] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-01] typed dict subscript を `.at()` 化し、`py_dict_get` の checked-in callsite を除去する。
- [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-02] tuple constant-index を generated/runtime path でも `std::get<N>` へ寄せ、tuple `py_at` helper を縮退または退役させる。
- [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-03] typed list/dict mutation helper を object bridge 専用 surface まで縮め、typed lane は emitter direct lowering を優先する。
- [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S4-01] `type_id` registry / subtype / isinstance の ownership を `py_tid_*` 主体へ寄せ、`py_runtime.h` の wrapper を薄くする。
- [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S4-02] `test_cpp_runtime_type_id.py` と generated runtime caller を更新し、cyclic ownership が再混入しないよう guard を追加する。
- [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S5-01] `py_isinstance_of` fast path、`PyFile` alias などの small cleanup を片付ける。
- [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S5-02] representative test / parity / docs / archive を更新して閉じる。

## 決定ログ

- 2026-03-09: 本計画は `py_runtime.h` の物理分割ではなく、「`core` に残す理由が弱い helper を explicit include / upstream / dedicated lane / generated SoT へ戻す」計画として扱う。
- 2026-03-09: first step は `type_id` ではなく `numeric_ops/zip_ops/contains` の explicit include 化とする。理由は、ここが最も低リスクに `core` 依存を減らせ、以後の inventory guard を置きやすいから。
- 2026-03-09: `py_dict_get` は過去 tranche で object dict / optional dict / string sugar を大半撤去済みであり、remaining debt は typed dict subscript が backend convenience として使っている 1 本に近い。したがって次の削減候補として優先度を高く置く。
- 2026-03-09: tuple helper は CppEmitter 本体では既に constant-index `std::get<N>` へ落ちているため、remaining caller は generated/runtime path の追従不足として扱う。
- 2026-03-09: `type_id` の end state は「`core` に raw primitive、generated 側に nominal subtype / registry algorithm」を基本形とし、手書き helper の延命は避ける。
- 2026-03-09: `S1-01` 棚卸しでは、`zip` の direct caller は `src/backends/cpp/emitter/runtime_expr.py`、`contains` の direct caller は `src/backends/cpp/emitter/cpp_emitter.py`、`numeric_ops` の public surface は `src/runtime/cpp/pytra/built_in/numeric_ops.h` であることを確認した。つまり include ownership の本命は `py_runtime.h` ではなく C++ emitter / generated caller / public companion header である。
- 2026-03-09: `py_dict_get` の checked-in caller は C++ emitter の typed dict path に加えて `src/runtime/cpp/generated/std/argparse.cpp`、`src/runtime/cpp/generated/built_in/type_id.cpp`、`selfhost/py2cpp.cpp` などの generated / selfhost path に残っていることを確認した。よって `S3-01` は emitter 側だけでなく generated caller 追従を前提に進める。
- 2026-03-09: `type_id` wrapper の checked-in caller は C++ backend 本体、generated C++ runtime、selfhost stage1/stage2、関連 test に広く残っているため、`S4-01` は「callsite を `py_tid_*` に寄せる / `py_runtime.h` wrapper を thin delegate に縮める」を同時に扱う slice とする。
- 2026-03-09: `S1-02` の契約として、`numeric_ops/zip_ops/contains` は `pytra/built_in/*.h` から explicit include される companion surface とし、`py_runtime.h` は再集約しない。typed dict / tuple constant-index / typed mutation helper は upstream または typed lane へ戻し、`core` に残るのは object bridge と low-level primitive だけに寄せる。非対象は他 target runtime の同時整理と boxing/unboxing の全面再設計で固定する。
- 2026-03-09: `S2-01` として `src/backends/cpp/emitter/module.py` の helper include collector を拡張し、`RuntimeSpecialOp(minmax)`、`runtime_call=zip/py_min/py_max`、direct `sum(...)` call、`Compare` の `In/NotIn` / lowered `Contains` から `pytra/built_in/{numeric_ops,zip_ops,contains}.h` を明示収集するようにした。`test_py2cpp_features.py` に回帰を追加し、transpiled C++ が `py_runtime.h` 以外からも必要 helper header を自力で引けることを固定した。
- 2026-03-09: `S2-02` として `src/runtime/cpp/native/core/py_runtime.h` から `numeric_ops` / `zip_ops` / `contains` の再集約 include を外し、tracked な generated caller（`generated/std/{re,json,argparse}.cpp`、`generated/built_in/type_id.cpp`）へ `pytra/built_in/contains.h` を明示追加した。`test_cpp_runtime_iterable.py` では compile snippet も explicit include へ切り替え、removed-include guard を `assertNotIn(...)` に反転して regression を固定した。
- 2026-03-09: `S3-01` として C++ emitter の typed dict subscript を lambda + `.at()` へ置き換え、string-key の any/unknown lane は既存 `py_at(dict, key)` へ寄せた。あわせて `generated/std/argparse.cpp` と `generated/built_in/type_id.cpp` の tracked caller を `.at()` へ更新し、`src/runtime/cpp/native/core/py_runtime.h` から generic `py_dict_get` helper を削除した。`test_east3_cpp_bridge.py` と runtime inventory test を更新し、tracked tree で `py_dict_get(` が再流入しない状態を固定した。
