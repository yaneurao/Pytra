# P0: C++ `py_runtime.h` argv state surface 縮退

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-ARGV-STATE-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)

背景:
- `py_runtime.h` 末尾には `py_runtime_argv_storage_v` と `py_runtime_argv_storage` / `py_runtime_set_argv` が残っている。
- 行数は小さいが、runtime state surface のうち compat 的な薄い helper が含まれている。
- `argv` state を最小 surface に揃えられるなら core をさらに薄くできる。

目的:
- `argv` state surface の compat helper を最小化し、不要な薄い sugar を退役する。

非対象:
- `pytra_configure_from_argv`
- stdout/stderr write helper
- runtime state そのものの別 header 分割

受け入れ基準:
- `argv` state の checked-in callsite が固定される。
- 削れる compat helper があれば退役し、残す surface は理由を決定ログに残す。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_*.py' -k argv`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`

## フェーズ

### Phase 1: 棚卸し
- checked-in callsite と残置理由を固定する。

### Phase 2: 最小化
- compat helper を削除または薄くする。

### Phase 3: 退役
- guard / docs / archive を更新して閉じる。

## タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-ARGV-STATE-01] argv state surface を最小化する。
- [ ] [ID: P0-CPP-PYRUNTIME-ARGV-STATE-01-S1-01] checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-ARGV-STATE-01-S1-02] 残す surface と削る surface を決定ログに固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-ARGV-STATE-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-ARGV-STATE-01-S2-02] compat helper を削除または最小化する。
- [ ] [ID: P0-CPP-PYRUNTIME-ARGV-STATE-01-S3-01] guard / docs / archive を更新して閉じる。

## 決定ログ

- 2026-03-09: 本計画は `argv` state surface の最小化のみを対象とし、runtime state の大規模再編は非対象とする。
- 2026-03-09: checked-in current callsite は `py_runtime_argv()` が `src/runtime/cpp/generated/std/argparse.cpp` と `src/runtime/cpp/native/std/sys.cpp`、`py_runtime_set_argv()` が `src/runtime/cpp/native/std/sys.cpp` と `pytra_configure_from_argv()` に限られる。
- 2026-03-09: canonical surface は `pytra_configure_from_argv()`, `py_runtime_argv()`, `py_runtime_set_argv()`, `py_runtime_write_stdout/stderr()`, `py_runtime_exit()` とし、`py_runtime_argv_storage()` accessor は compat sugar として削除する。
