<a href="../../../en/plans/archive/20260314-p1-nes3-not-implemented-error-cpp-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: `NotImplementedError` を C++ lane で未定義シンボルにしない

最終更新: 2026-03-14

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-NES3-NOT-IMPLEMENTED-ERROR-CPP-01`

背景:
- Pytra-NES3 の minimal repro [`materials/refs/from-Pytra-NES3/not_implemented_error.py`](../../../materials/refs/from-Pytra-NES3/not_implemented_error.py) は `raise NotImplementedError("todo")` だけで C++ compile failure を再現する。
- 2026-03-13 時点の generated C++ は `throw NotImplementedError(...)` をそのまま emit し、C++ 側に定義がないため build できない。
- `bus_port_pkg/` でも同じ例外シンボルが surface に漏れており、この residual は個別 fixture を超えて shared blocker になっている。

目的:
- C++ lane で Python `NotImplementedError` を未定義の生シンボルへ lower しない contract に揃える。
- minimal repro と shared consumer fixture の両方で再発しないよう regression を固定する。

対象:
- `NotImplementedError` の frontend / lowering / emitter / runtime mapping
- `materials/refs/from-Pytra-NES3/not_implemented_error.py` の compile smoke
- shared residual を参照する fixture の focused regression / docs / TODO

非対象:
- Python exception hierarchy の全面実装
- `ValueError` など他例外クラスの同時 rollout
- non-C++ backend への横展開

受け入れ基準:
- `not_implemented_error.py` の generated C++ が compile できる。
- `bus_port_pkg` など同じ residual で `NotImplementedError` が未定義になる経路が残らない。
- fix lane が regression / plan / TODO に記録される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `bash ./pytra materials/refs/from-Pytra-NES3/not_implemented_error.py --target cpp --output-dir /tmp/pytra_nes3_not_implemented_error`
- `g++ -std=c++20 -O0 -c /tmp/pytra_nes3_not_implemented_error/src/not_implemented_error.cpp -I /tmp/pytra_nes3_not_implemented_error/include -I /workspace/Pytra/src -I /workspace/Pytra/src/runtime/cpp`
- `git diff --check`

## 分解

- [x] [ID: P1-NES3-NOT-IMPLEMENTED-ERROR-CPP-01-S1-01] current compile failure と desired C++ contract を focused regression / plan / TODO に固定する。
- [x] [ID: P1-NES3-NOT-IMPLEMENTED-ERROR-CPP-01-S2-01] `NotImplementedError` の lowering / runtime mapping を追加し、未定義生シンボル emission を止める。
- [x] [ID: P1-NES3-NOT-IMPLEMENTED-ERROR-CPP-01-S3-01] minimal repro と shared 影響 lane の compile smoke / docs を同期する。

決定ログ:
- 2026-03-13: Pytra-NES3 bug report から起票。shared residual を個別に追えるよう独立した P1 task とする。
- 2026-03-14: `NotImplementedError` を exception ctor builtin 分類 / return type 推論 / C++ profile type map / runtime alias へ追加し、`raise NotImplementedError(...)` が未 lower の生シンボルではなく `::std::runtime_error` 系 surface へ流れるようにした。
- 2026-03-14: focused regression として `not_implemented_error.py` の syntax-check、および shared consumer として `bus_port_pkg` multi-file compile check を追加し、`python3 src/py2x.py --target cpp`・`bash ./pytra ... --target cpp --output-dir ...`・`g++ -c` がすべて green な状態で close した。
