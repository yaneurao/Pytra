<a href="../../../en/plans/archive/20260312-p0-bytes-truthiness-cpp-representative-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `bytes` truthiness representative C++ support

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-BYTES-TRUTHINESS-CPP-REPRESENTATIVE-01`

背景:
- Pytra-NES から共有された minimal sample [`materials/refs/from-Pytra-NES/bytes_truthiness.py`](../../../materials/refs/from-Pytra-NES/bytes_truthiness.py) は `if payload:` のような `bytes` truthiness を使う。
- 現状の representative C++ lane では `bytes` が `const list<unsigned char>` として lower される一方、truthiness は `if (payload)` のまま出てしまい、C++ build が `could not convert ... to bool` で失敗する。
- これは `~` や `deque` のような別 task ではなく、`bytes` 専用 truthiness lowering の不足である。

目的:
- `bytes` truthiness を representative C++ lane で正しく lower し、Pytra-NES の blocker を外す。
- `bytes` が `bool` へ暗黙変換される前提を消し、truthiness contract を focused regression と inventory に固定する。

対象:
- `if payload:` / `while payload:` / conditional expression における `bytes` truthiness
- representative C++ emitter/lowering
- focused regression / docs / TODO の同期

非対象:
- Python の truthiness 全般の redesign
- `bytes` runtime 型そのものの redesign
- non-C++ backend への同時 rollout
- `bytearray` や `memoryview` への自動拡張

受け入れ基準:
- minimal sample `bytes_truthiness.py` の current failure が focused regression で固定される。
- representative C++ lane で `bytes` truthiness が `len` / helper 経由へ lower され、compile smoke が通る。
- `bytes` truthiness の support wording が plan / TODO に記録される。
- 後続で `bytearray` などを別 task として切り出せる粒度になっている。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k bytes_truthiness`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_east3_cpp_bridge.py' -k truthy`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: Pytra-NES blocker は compile failure であり、runtime redesign ではなく representative C++ lowering で先に外す。
- 2026-03-12: v1 は `bytes` に限定し、`bytearray` などの拡張は後段へ回す。
- 2026-03-12: `IfExp` だけは `CppEmitter._render_ifexp_expr()` が `render_expr(test)` を使っていて `payload ? 1 : 0` を漏らしていたため、`render_cond(test)` へ切り替えて `x if payload else y` も `py_len(payload) != 0` を通る representative contract に揃えた。
- 2026-03-12: C++ support docs の `bytes / bytearray` 行へ representative `bytes` truthiness support wording を追加し、この task を archive へ移した。

## 分解

- [x] [ID: P0-BYTES-TRUTHINESS-CPP-REPRESENTATIVE-01] `bytes` truthiness の representative C++ lane を固定し、Pytra-NES blocker を外す。
- [x] [ID: P0-BYTES-TRUTHINESS-CPP-REPRESENTATIVE-01-S1-01] minimal sample baseline と current C++ failure を focused regression / TODO / plan に固定する。
- [x] [ID: P0-BYTES-TRUTHINESS-CPP-REPRESENTATIVE-01-S2-01] representative C++ lane で `bytes` truthiness を helper / `len` ベースに lower する。
- [x] [ID: P0-BYTES-TRUTHINESS-CPP-REPRESENTATIVE-01-S3-01] docs / support wording / regression を current contract に同期して閉じる。

- 2026-03-12: `S1-01/S2-01` として representative fixture `test/fixtures/typing/bytes_truthiness.py` を追加し、`if payload` / `while payload` / conditional expression の regression を C++ runtime smoke で固定した。C++ emitter の `render_cond` は `bytes` を `py_len(...) != 0` へ lower するように更新した。
- 2026-03-12: `S3-01` として `IfExp` も `render_cond(test)` 経由に統一し、support docs / TODO / archive handoff を current representative contract に同期して task 全体を完了扱いにした。
