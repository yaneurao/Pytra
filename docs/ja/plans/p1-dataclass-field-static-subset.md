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
- `python3 tools/check_todo_priority.py`、focused unit tests、`python3 tools/build_selfhost.py`、`git diff --check` が通ること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_diagnostics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k dataclass`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: `field(...)` は runtime function として扱わず、compile-time の dataclass metadata subset として吸収する方針にした。reflection や dynamic typing は導入しない。
- 2026-03-12: v1 subset は `default` / `default_factory` / `init` / `repr` / `compare` に限定し、それ以外は fail-closed とする。
- 2026-03-12: `default_factory` は first pass では representative zero-arg factory を中心に扱い、任意 callable の全面許可は後段に回す。
- 2026-03-12: `deque[T]` の backend support 自体は別論点なので、この task では「`field(...)` が式として漏れないこと」を先に固定する。

## 分解

- [ ] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S1-01] representative failure と scope を regression / docs で固定する。
- [ ] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S2-01] frontend / lowering で `field(...)` を静的 metadata carrier へ吸収する。
- [ ] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S2-02] `init` / `default` / `default_factory` の constructor / field-init contract を固定する。
- [ ] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S3-01] `repr` / `compare` の metadata lane と unsupported option の fail-closed policy を固定する。
- [ ] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S3-02] docs / TODO / regression / inventory を同期して task を閉じる。
