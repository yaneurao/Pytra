<a href="../../../en/plans/archive/20260312-p0-dataclass-field-default-factory-rc-cpp-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `field(default_factory=...)` rc field representative C++ support

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-DATACLASS-FIELD-DEFAULT-FACTORY-RC-CPP-01`

背景:
- Pytra-NES の minimal sample [`materials/refs/from-Pytra-NES/field_default_factory_rc_obj.py`](../../../materials/refs/from-Pytra-NES/field_default_factory_rc_obj.py) は `field(default_factory=Child)` を `rc<Child>` field に使う。
- 現状の representative C++ lane では `Parent(rc<Child> child = Child())` のような invalid default arg が emit され、`Child` を `rc<Child>` に変換できず build failure になる。
- `field(...)` を static metadata として吸収する前段 task は既に進んでいるため、ここでの本丸は `default_factory` の rc lane lowering である。

目的:
- representative C++ lane で `field(default_factory=...)` を rc field に対して正しく lower し、Pytra-NES blocker を外す。
- dataclass metadata の `default_factory` が value lane と rc lane で異なる lowering を取ることを current contract として固定する。

対象:
- dataclass field metadata の `default_factory`
- representative C++ rc field lane
- focused regression / docs / TODO の同期

非対象:
- Python dataclasses 完全互換
- arbitrary callable `default_factory`
- non-C++ backend への同時 rollout
- `field(metadata=...)` や reflection 的機能

受け入れ基準:
- minimal sample `field_default_factory_rc_obj.py` の current failure が focused regression で固定される。
- representative C++ lane で rc field の `default_factory=Child` が `::rc_new<Child>()` 相当の正しい lane に lower され、compile smoke が通る。
- value lane と rc lane の lowering 差分が regression と docs に記録される。
- `default_factory` representative subset の current contract が plan / TODO に明記される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k dataclass_field`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core_parser_behavior_classes.py' -k field`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: この task は `field(...)` 全体ではなく、Pytra-NES blocker である representative `default_factory` rc lane に限定する。
- 2026-03-12: v1 は zero-arg class factory の representative subset を対象にし、arbitrary callable は fail-closed のまま維持する。

## 分解

- [x] [ID: P0-DATACLASS-FIELD-DEFAULT-FACTORY-RC-CPP-01] `field(default_factory=...)` の rc field lane を representative C++ contract に揃え、Pytra-NES blocker を外す。
- [x] [ID: P0-DATACLASS-FIELD-DEFAULT-FACTORY-RC-CPP-01-S1-01] minimal sample baseline と current C++ failure を focused regression / TODO / plan に固定する。
- [x] [ID: P0-DATACLASS-FIELD-DEFAULT-FACTORY-RC-CPP-01-S2-01] representative C++ rc field lane で `default_factory` を正しい ctor / member-init lowering に揃える。
- [x] [ID: P0-DATACLASS-FIELD-DEFAULT-FACTORY-RC-CPP-01-S3-01] docs / support wording / representative subset regression を current contract に同期して閉じる。

- 2026-03-12: representative C++ lane では `field(default_factory=Child)` かつ field 型が `rc<...>` lane のとき、ctor default/member-init を `::rc_new<Child>()` に lower する current contract で固定した。
- 2026-03-12: representative static dataclass subset は `default`、`default_factory=deque`、`default_factory=Child` on `rc<Child>` までを support docs と parser/C++ regression で固定し、arbitrary callable `default_factory` は対象外のまま残す。
