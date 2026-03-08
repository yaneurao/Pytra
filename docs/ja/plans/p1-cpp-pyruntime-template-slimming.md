# P1: C++ `py_runtime.h` を `@template` ベースで縮退させる

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01`

関連:
- [archive/20260308-p1-cpp-py-runtime-core-slimming.md](./archive/20260308-p1-cpp-py-runtime-core-slimming.md)
- [archive/20260308-p2-linked-runtime-helper-template-v1.md](./archive/20260308-p2-linked-runtime-helper-template-v1.md)
- [p2-runtime-sot-linked-program-integration.md](./p2-runtime-sot-linked-program-integration.md)
- [p2-runtime-helper-generics-under-linked-program.md](./p2-runtime-helper-generics-under-linked-program.md)
- [../spec/spec-template.md](../spec/spec-template.md)
- [../spec/spec-runtime.md](../spec/spec-runtime.md)
- [../spec/spec-abi.md](../spec/spec-abi.md)

背景:
- 2026-03-08 時点で `@template("T", ...)` は linked runtime helper 向け generic surface の canonical syntax として方針固定済みだが、実装はまだ入っていない。
- 一方、`src/runtime/cpp/native/core/py_runtime.h` には、`sum`, `min`, `max`, `zip`, `sorted` のような高水準 helper や collection/string helper の残骸がまだ多く、low-level glue へ縮退し切れていない。
- 以前の `P1-CPP-PY-RUNTIME-SLIM-01` で string helper 第一波は `generated/built_in` へ戻したが、generic を必要とする helper は `@template` と linked-program specialization が無いと pure Python SoT へ戻しにくい。
- `@abi` は generated helper 境界を固定する実務解として有効だが、helper 自体を ordinary module として linked-program optimizer に載せ、さらに generic 化できるなら、`@abi` を helper ごとに増やすより自然で、より積極的な最適化も可能になる。
- したがって次段は「`@template` を runtime helper 限定で実装し、その lane を使って `py_runtime.h` の generic helper を SoT 側へ戻す」計画として扱うのがよい。

目的:
- runtime helper 限定の `@template("T", ...)` を実装し、linked-program 段で implicit specialization できる最小 lane を作る。
- `py_runtime.h` に残っている generic helper 候補を pure Python SoT 側へ戻し、C++ では generated helper として使う。
- `native/core/py_runtime.h` を low-level ABI / object / container / process glue 中心へさらに縮退させる。
- generic helper を `object` 退化や target 固有 hand-written helper へ逃がさず、typed specialization 前提で扱えるようにする。

対象:
- `@template("T", ...)` の parser / EAST / linked metadata / validator / specialization collector / monomorphization
- runtime helper 限定の generic function 実装
- `src/pytra/built_in/*.py` への generic helper 追加
- C++ runtime generation と `py_runtime.h` からの helper 撤去
- representative C++ backend/runtime/parity tests
- `docs/ja/spec/{spec-template,spec-runtime,spec-abi,spec-east,spec-linker}.md`

非対象:
- user code 全般への generic/template 一般公開
- `@instantiate(...)` の導入
- generic class / method / nested generic
- 全 backend 同時対応
- `PyObj` / `object` / `rc<>` / `type_id` / low-level dynamic bridge の SoT 化
- `py_runtime.h` を 1 回で空にすること

受け入れ基準:
- runtime helper 限定で `@template("T", ...)` が実装され、linked-program 段で deterministic に specialization される。
- specialization collector は raw decorator ではなく `FunctionDef.meta.template_v1` を正本にする。
- `sum`, `min`, `max`, `zip`, `sorted` のうち少なくとも 2 系統以上が pure Python SoT 側へ移り、C++ では specialized generated helper を使う。
- `native/core/py_runtime.h` から、上記 helper に対応する高水準実装が撤去される。
- C++ backend / runtime unit / fixture parity / sample parity が非退行で通る。
- docs 上で「`@template` を何のために導入したか」と「`py_runtime.h` から何をどこへ移すか」の責務境界が明文化される。

依存関係:
- `@template` v1 syntax decision は完了済みとする。
- linked-program optimizer の基本導線は既に完了済みとする。
- `runtime SoT linked-program integration` の本命案は将来残るが、本計画では runtime helper 限定の最小 lane を先行実装してよい。
- `@abi` は helper 境界の補助として維持するが、本計画では generic helper の primary mechanism にはしない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_runtime_cpp_layout.py`
- `python3 tools/check_runtime_core_gen_markers.py`
- `python3 tools/gen_runtime_symbol_index.py --check`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_*template*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/link -p 'test_*template*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_*.py'`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

## 1. 問題の本質

問題は `py_runtime.h` が大きいことではなく、「generic を必要とする helper を SoT に戻す lane が無いので、C++ native core に残り続ける」ことにある。

いま string helper 第一波は戻せているが、次の helper は generic support が無いと戻しづらい。

- `sum`
- `min`
- `max`
- `zip`
- `sorted`
- 今後の `head/take/keys/values/items` 系 helper

これらを hand-written C++ に残すと:

- 他言語と SoT を共有しにくい
- backend ごとに最適化方針が分散する
- `object` 退化か hand-written template に逃げやすい
- `py_runtime.h` の縮退が止まる

したがって、`@template` を runtime helper 限定で実装し、その lane を使って generic helper を pure Python SoT へ戻すのが本質解になる。

## 2. 基本方針

1. `@template("T", ...)` は runtime helper の top-level function 限定で実装する。
2. explicit instantiation は入れず、linked-program 段で callsite から implicit specialization する。
3. generic helper の実体は `src/pytra/built_in/*.py` を正本とし、C++ では specialization 後の generated helper を使う。
4. `native/core/py_runtime.h` は低レベル glue に限定し、generic helper の正本を置かない。
5. `@abi` は必要な boundary case にだけ残し、generic helper の primary mechanism にしない。

## 3. `py_runtime.h` から戻す候補

第一波候補:
- `sum`
- `min`
- `max`

第二波候補:
- `zip`
- `sorted`

保留候補:
- `dict.keys` / `dict.values` / `dict.items`
- `take/head/tail`
- object bridge を強く噛む helper

分類基準:
- generic parameter だけで表現できる helperは `@template` 候補
- `object` / `std::any` / dynamic dispatch を本質的に必要とする helper は保留
- `rc<>` / `type_id` / process I/O / OS glue は `native/core` に残す

## 4. 実装戦略

### Phase 1: inventory と契約固定

- `py_runtime.h` に残る generic helper 候補を棚卸しする。
- `spec-template` / `spec-runtime` / `spec-east` / `spec-linker` に helper-limited `@template` の責務境界を反映する。
- specialization 命名、collector 入口、invalid case の diagnostics 方針を決める。

### Phase 2: `@template` 最小実装

- parser で `@template("T", ...)` を受理する。
- `FunctionDef.meta.template_v1` を正本 metadata にする。
- validator で `runtime helper only` / `top-level function only` / duplicate param 禁止を enforce する。
- linked-program 側で specialization collector と monomorphization の最小実装を入れる。

### Phase 3: generic helper の SoT 移管

- `src/pytra/built_in/*.py` に generic helper を追加する。
- representative helper を specialized generated helper として C++ へ出す。
- `native/core/py_runtime.h` から対応する hand-written helper を撤去する。

### Phase 4: regression 固定

- runtime symbol index / build graph / emitter / runtime tests を追従させる。
- fixture/sample parity を再実行し、非退行を固定する。
- docs と decision log を同期する。

## 5. タスク分解

- [ ] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01] `@template` を runtime helper 限定で実装し、generic helper を pure Python SoT 側へ戻すことで C++ `py_runtime.h` を縮退させる。
- [ ] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S1-01] `py_runtime.h` に残る generic helper 候補を棚卸しし、第一波 / 第二波 / 保留へ分類する。
- [ ] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S1-02] `spec-template` / `spec-runtime` / `spec-east` / `spec-linker` に helper-limited `@template` の責務境界と specialization 契約を追記する。
- [ ] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S2-01] parser / EAST metadata / validator で `@template("T", ...)` を runtime helper 限定で受理する。
- [ ] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S2-02] linked-program 側に specialization collector と monomorphization の最小実装を入れる。
- [ ] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S3-01] `sum` / `min` / `max` を pure Python generic helper として SoT 側へ移し、C++ generated helper へ切り替える。
- [ ] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S3-02] `zip` / `sorted` のうち少なくとも 1 系統以上を同様に移し、`py_runtime.h` から hand-written helper を撤去する。
- [ ] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S4-01] runtime symbol index / build graph / representative backend/runtime tests を新 contract へ追従させる。
- [ ] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S4-02] fixture/sample parity・docs 同期・必要な guard 追加まで完了し、本計画を閉じる。

## 6. 決定ログ

- 2026-03-08: `@template("T", ...)` の syntax decision は完了済みとし、本計画は「syntax 決定」ではなく「実装して `py_runtime.h` を減らす」フェーズとして扱う。
- 2026-03-08: `@abi` は helper 境界の補助として残るが、generic helper を戻す主手段にはしない。generic helper は linked-program ordinary call として specialization する。
- 2026-03-08: 最初から全 helper を generic 化せず、`sum/min/max` を第一波、`zip/sorted` を第二波に分けて進める。
