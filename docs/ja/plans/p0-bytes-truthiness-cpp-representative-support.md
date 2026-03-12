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
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k bytes_truthiness`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py' -k truthy`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: Pytra-NES blocker は compile failure であり、runtime redesign ではなく representative C++ lowering で先に外す。
- 2026-03-12: v1 は `bytes` に限定し、`bytearray` などの拡張は後段へ回す。

## 分解

- [ ] [ID: P0-BYTES-TRUTHINESS-CPP-REPRESENTATIVE-01] `bytes` truthiness の representative C++ lane を固定し、Pytra-NES blocker を外す。
- [ ] [ID: P0-BYTES-TRUTHINESS-CPP-REPRESENTATIVE-01-S1-01] minimal sample baseline と current C++ failure を focused regression / TODO / plan に固定する。
- [ ] [ID: P0-BYTES-TRUTHINESS-CPP-REPRESENTATIVE-01-S2-01] representative C++ lane で `bytes` truthiness を helper / `len` ベースに lower する。
- [ ] [ID: P0-BYTES-TRUTHINESS-CPP-REPRESENTATIVE-01-S3-01] docs / support wording / regression を current contract に同期して閉じる。
