# P0: C++ `py_runtime.h` process surface を専用laneへ再配置する

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-PROCESS-SURFACE-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)

背景:
- `py_runtime.h` 末尾には `py_runtime_argv_storage_v`, `py_runtime_argv()`, `py_runtime_set_argv()`, `py_runtime_write_stdout()`, `py_runtime_write_stderr()`, `py_runtime_exit()` が残っている。
- これは object runtime の中核というより process / host interaction surface であり、`py_runtime.h` に残ることで core runtime の責務が広く見えている。
- 行数削減だけでなく、他 target runtime 実装時に process surface と object runtime を混同しないようにしたい。

目的:
- `argv/stdout/stderr/exit` の process surface を `py_runtime.h` から外し、dedicated lane へ再配置する。

非対象:
- `pytra_configure_from_argv` の意味変更
- stdout/stderr の I/O policy 変更
- runtime state 全体の大規模再編

受け入れ基準:
- `py_runtime.h` から `py_runtime_argv()`, `py_runtime_set_argv()`, `py_runtime_write_stdout()`, `py_runtime_write_stderr()`, `py_runtime_exit()` が外れる。
- checked-in caller は new process lane header に追従する。
- representative runtime / backend test が非退行で通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_*cpp*' -k argv -v`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`

## 1. 方針

1. process surface の checked-in caller を棚卸しする。
2. `py_runtime.h` には low-level object runtime だけを残し、process / argv / stdout / stderr / exit は dedicated lane へ移す。
3. 旧 surface を compat alias として `py_runtime.h` に残さない。

## 2. フェーズ

### Phase 1: 棚卸し
- `argv` / `stdout` / `stderr` / `exit` surface の checked-in caller と include 依存を固定する。

### Phase 2: 再配置
- dedicated lane を用意し、representative caller を new include へ追従させる。
- regression / inventory guard を追加する。

### Phase 3: 退役
- `py_runtime.h` から process surface を削除し、parity / docs / archive を閉じる。

## 3. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-PROCESS-SURFACE-01] process surface を専用laneへ再配置する。
- [ ] [ID: P0-CPP-PYRUNTIME-PROCESS-SURFACE-01-S1-01] `argv/stdout/stderr/exit` surface の checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-PROCESS-SURFACE-01-S1-02] dedicated lane と non-goal を決定ログに固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-PROCESS-SURFACE-01-S2-01] representative caller を新契約へ置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-PROCESS-SURFACE-01-S2-02] regression / inventory guard を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-PROCESS-SURFACE-01-S3-01] `py_runtime.h` から process surface を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-PROCESS-SURFACE-01-S3-02] parity / docs / archive を更新して閉じる。

## 4. 決定ログ

- 2026-03-09: 本計画は process / argv surface の dedicated lane 化を目的とし、`pytra_configure_from_argv` の意味変更や runtime state policy の再設計は非対象とする。
- 2026-03-09: dedicated lane は `runtime/cpp/core/process_runtime.h` / `runtime/cpp/native/core/process_runtime.h` の header-only surface とし、`py_runtime.h` には compat alias を残さない。
- 2026-03-09: checked-in direct caller は `native/std/sys.cpp`, `generated/std/argparse.cpp`, `CPP_HEADER`, multi-file prelude に限られ、`runtime_calls.json` の surface 名は維持する。
