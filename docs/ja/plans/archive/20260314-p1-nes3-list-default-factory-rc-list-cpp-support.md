<a href="../../../en/plans/archive/20260314-p1-nes3-list-default-factory-rc-list-cpp-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: `field(default_factory=lambda: [0] * N)` の `rc<list<T>>` lane を C++ で整合させる

最終更新: 2026-03-14

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-NES3-LIST-DEFAULT-FACTORY-RC-LIST-CPP-01`

背景:
- Pytra-NES3 repro [`materials/refs/from-Pytra-NES3/list_default_factory.py`](../../../materials/refs/from-Pytra-NES3/list_default_factory.py) は `field(default_factory=lambda: [0] * 8)` を `rc<list<int64>>` field に使う。
- archived task で `field(default_factory=Child)` on `rc<Child>` は representative support 済みだが、2026-03-13 時点の C++ lane では list factory が `list<int64>` value のまま emit され、`rc<list<int64>>` と不整合になる。
- さらに default arg 位置で capture-default lambda を生成しており、C++ としても不正なコードになる。

目的:
- `rc<list<T>>` field に対する zero-capture list factory を representative subset として通す。
- `default_factory` の value lane と `rc<list<T>>` lane の差分を compile smoke と regression で固定する。

対象:
- dataclass field metadata の `default_factory=lambda: [0] * N`
- `rc<list<T>>` ctor default / member-init lane
- `materials/refs/from-Pytra-NES3/list_default_factory.py` の compile smoke
- regression / docs / TODO 同期

非対象:
- arbitrary callable `default_factory` 全般
- capture 付き closure factory
- non-C++ backend への同時 rollout

受け入れ基準:
- `list_default_factory.py` の generated C++ が compile できる。
- generated code が `list<T>` value をそのまま `rc<list<T>>` に渡さず、representative contract に合う形へ lower される。
- 既存の `default_factory=Child` / `default_factory=deque` lane を壊さない。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `bash ./pytra materials/refs/from-Pytra-NES3/list_default_factory.py --target cpp --output-dir /tmp/pytra_nes3_list_default_factory`
- `g++ -std=c++20 -O0 -c /tmp/pytra_nes3_list_default_factory/src/list_default_factory.cpp -I /tmp/pytra_nes3_list_default_factory/include -I /workspace/Pytra/src -I /workspace/Pytra/src/runtime/cpp`
- `git diff --check`

## 分解

- [x] [ID: P1-NES3-LIST-DEFAULT-FACTORY-RC-LIST-CPP-01-S1-01] current compile failure と representative subset 境界を focused regression / plan / TODO に固定した。
- [x] [ID: P1-NES3-LIST-DEFAULT-FACTORY-RC-LIST-CPP-01-S2-01] `rc<list<T>>` lane の `default_factory=lambda: [0] * N` を正しい ctor / member-init lowering へ揃えた。
- [x] [ID: P1-NES3-LIST-DEFAULT-FACTORY-RC-LIST-CPP-01-S3-01] compile smoke と docs wording を current subset contract に同期した。

決定ログ:
- 2026-03-13: archived `default_factory` representative supportの続きとして、`rc<list<T>>` list factory だけを個別に追う。
- 2026-03-14: dataclass field default_factory は rendered expression を field type に再整形する helper を通すようにし、zero-capture lambda は body を直接 `rc_list_from_value(...)` へ寄せる方針にした。
- 2026-03-14: focused regression `test_cli_pytra_nes3_list_default_factory_rc_list_syntax_checks` を追加し、`python3 src/py2x.py --target cpp --multi-file --output-dir /tmp/pytra_nes3_list_default_factory_py2x` と selfhosted `bash ./pytra ... --target cpp --output-dir /tmp/pytra_nes3_list_default_factory_selfhost` の両 lane で compile green を確認した。
