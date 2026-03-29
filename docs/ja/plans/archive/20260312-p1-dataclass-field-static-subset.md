<a href="../../../en/plans/archive/20260312-p1-dataclass-field-static-subset.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: static dataclass `field(...)` subset

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01`

背景:
- Pytra-NES では `timestamps: deque[float] = field(init=False, repr=False)` のような `dataclasses.field(...)` usage が現れている。
- 現状の Pytra は `field(...)` を dataclass metadata として吸収せず、通常の式・関数呼び出しとして backend へ流してしまう。
- その結果、representative C++ lane では `field(false, false)` のような壊れた constructor/default emit になり、実験の blocker になっている。
- ただしここで必要なのは reflection や runtime field introspection ではなく、compile-time の dataclass metadata subset だけである。

目的:
- `dataclasses.field(...)` を runtime call ではなく静的 dataclass metadata として扱う。
- v1 では `default` / `default_factory` / `init` / `repr` / `compare` を正式 subset とし、representative lane を backend policy つきで固定する。
- unsupported option は silent fallback せず fail-closed にする。

対象:
- `field(...)` call の frontend / lowering での静的 metadata 吸収
- dataclass field carrier における `default` / `default_factory` / `init` / `repr` / `compare` の保持
- representative constructor generation / field initialization policy
- representative backend で `field(...)` call を runtime emit しない contract
- unsupported option / unsupported factory の fail-closed regression

非対象:
- dataclass field reflection / runtime metadata API
- Python dataclasses の full parity
- `metadata`, `hash`, `kw_only` などの高度な option
- 任意 callable 全般を `default_factory` として許可すること
- `deque[T]` 自体の backend support を先回りで全面解決すること

受け入れ基準:
- representative case で `field(...)` が通常の式として backend 出力へ漏れないこと。
- `init=False` が constructor 生成に反映されること。
- `default` / `default_factory` / `repr` / `compare` の v1 subset が field carrier に乗ること。
- unsupported option は明示的に fail-closed すること。
- `python3 tools/check/check_todo_priority.py`、focused unit tests、`python3 tools/build_selfhost.py`、`git diff --check` が通ること。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_import_diagnostics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k dataclass`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: `field(...)` は runtime function として扱わず、compile-time の dataclass metadata subset として吸収する方針にした。reflection や dynamic typing は導入しない。
- 2026-03-12: v1 subset は `default` / `default_factory` / `init` / `repr` / `compare` に限定し、それ以外は fail-closed とする。
- 2026-03-12: `default_factory` は first pass では representative zero-arg factory を中心に扱い、任意 callable の全面許可は後段に回す。
- 2026-03-12: `deque[T]` の backend support 自体は別論点なので、この task では「`field(...)` が式として漏れないこと」を先に固定する。
- 2026-03-12: `timestamps: deque[float] = field(init=False, repr=False)` の baseline を確認した。初期状態では parser が `field(...)` を plain `Call(Name("field"))` のまま保持し、C++ backend は `deque[float64] timestamps;` と `field(false, false)` を emit していた。
- 2026-03-12: `S2-01` として class-body `AnnAssign` parsing に `core_dataclass_field_semantics.py` を追加し、representative `field(...)` call は `AnnAssign.meta.dataclass_field_v1` へ吸収し、`value` は backend に流さない形へ変えた。`default` / `default_factory` / `init` / `repr` / `compare` は metadata に保持する。
- 2026-03-12: `S2-02` として C++ dataclass auto-constructor が `meta.dataclass_field_v1` を参照するようにし、`init=False` field は ctor param から除外し、`default` / `default_factory` は representative lane で ctor default または member init として使うようにした。
- 2026-03-12: `S3-01` として `repr` / `compare` metadata の representative regression と、unsupported option / duplicate option / `default` + `default_factory` 併用の fail-closed regression を固定した。C++ representative lane でも `field(...)` call や metadata key が leak しないことを確認した。
- 2026-03-12: `S3-02` として dataclass field semantics source-contract を独立 test へ分離し、helper surface / module parser integration / docs を同期して task を close-ready にした。

## 分解

- [x] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S1-01] representative failure と scope を regression / docs で固定する。
- [x] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S2-01] frontend / lowering で `field(...)` を静的 metadata carrier へ吸収する。
- [x] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S2-02] `init` / `default` / `default_factory` の constructor / field-init contract を固定する。
- [x] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S3-01] `repr` / `compare` の metadata lane と unsupported option の fail-closed policy を固定する。
- [x] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S3-02] docs / TODO / regression / inventory を同期して task を閉じる。
