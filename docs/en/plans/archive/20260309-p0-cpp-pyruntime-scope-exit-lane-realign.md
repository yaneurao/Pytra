<a href="../../ja/plans/archive/20260309-p0-cpp-pyruntime-scope-exit-lane-realign.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-scope-exit-lane-realign.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-scope-exit-lane-realign.md`

# P0: C++ `py_runtime.h` `py_make_scope_exit` を専用laneへ再配置する

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-SCOPEEXIT-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)

背景:
- `py_make_scope_exit` は low-level object runtime というより RAII utility であり、`py_runtime.h` に直置きされているのは責務上のノイズになっている。
- 行数の削減量自体は小さいが、他言語 runtime を書くときに「object runtime に scope-exit utility まで含めるべきか」という誤学習を招く。

目的:
- `py_make_scope_exit` を `py_runtime.h` から外し、より責務の明確な dedicated lane へ移すか、caller 側へ inline する。

非対象:
- C++ 全体の utility header 再編
- scope-exit 自体の削除
- process / argv surface の再編

受け入れ基準:
- `py_runtime.h` に `py_make_scope_exit` が残らない。
- checked-in caller は dedicated lane か inline 実装へ追従する。
- representative test / build graph が非退行で通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_*.py' -v`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`

## 1. 方針

1. `py_make_scope_exit` の checked-in caller を棚卸しする。
2. generic RAII utility は core object runtime から外し、dedicated lane へ再配置する。
3. helper 名の互換 alias を `py_runtime.h` に残さない。

## 2. フェーズ

### Phase 1: 棚卸し
- checked-in callsite と include 依存を固定する。

### Phase 2: 再配置
- representative caller を new lane または inline 実装へ追従させる。
- regression / inventory guard を追加する。

### Phase 3: 退役
- `py_runtime.h` から helper を削除し、docs / archive を同期する。

## 3. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-SCOPEEXIT-01] `py_make_scope_exit` を専用laneへ再配置する。
- [ ] [ID: P0-CPP-PYRUNTIME-SCOPEEXIT-01-S1-01] `py_make_scope_exit` の checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-SCOPEEXIT-01-S1-02] new lane と non-goal を決定ログに固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-SCOPEEXIT-01-S2-01] representative caller を新契約へ置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-SCOPEEXIT-01-S2-02] regression / inventory guard を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-SCOPEEXIT-01-S3-01] `py_runtime.h` から `py_make_scope_exit` を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-SCOPEEXIT-01-S3-02] parity / docs / archive を更新して閉じる。

## 4. 決定ログ

- 2026-03-09: 本計画は `py_make_scope_exit` を core object runtime から外すことを目的とし、scope-exit utility 自体の削除は目的にしない。
- 2026-03-09: dedicated lane は `runtime/cpp/core/scope_exit.h` / `runtime/cpp/native/core/scope_exit.h` の header-only utility とし、`CPP_HEADER` と multi-file prelude が明示的に include する契約で固定した。
- 2026-03-09: checked-in direct caller は `generated/std/pathlib.cpp`, `generated/utils/gif.cpp`, `generated/utils/png.cpp`, `cpp_emitter` の `scope_exit_open` fragment に限られ、`py_runtime.h` には compat alias を残さないと決めた。
