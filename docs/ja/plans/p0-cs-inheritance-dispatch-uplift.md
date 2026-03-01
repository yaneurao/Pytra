# P0: C# 継承メソッド動的ディスパッチ改善

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-CS`

背景:
- `CSharpEmitter` はクラス継承を出力するが、メソッドの `virtual/override` と `super()` 呼び出し lower が不足している。

目的:
- 基底型参照経由のメソッド呼び出しで Python 相当の動的ディスパッチを成立させる。

対象:
- `src/hooks/cs/emitter/cs_emitter.py`
- `test/fixtures/oop/inheritance_virtual_dispatch_multilang.py`

非対象:
- C# selfhost 全体の完走

受け入れ基準:
- 基底メソッドに `virtual`、派生オーバーライドに `override` が出力される。
- `super().method(...)` / `super().__init__(...)` が C# 有効構文に lower される。
- fixture parity が一致する。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets cs`

分解:
- [x] 基底メソッドオーバーライド関係を事前解析し、メソッド宣言へ `virtual/override` を付与する。
- [x] `super()` 呼び出しを `base` 呼び出しへ lower する。
- [x] fixture の transpile + parity 回帰を追加する。

決定ログ:
- 2026-03-01: C# を最優先対象の一つとして独立 plan 化した。
- 2026-03-01: `CSharpEmitter` に継承メソッド解析（`class_method_map` / `class_children_map`）を追加し、基底定義ありは `override`、派生再定義ありは `virtual` を付与するようにした。
- 2026-03-01: `super().method(...)` を `base.method(...)` へ lower、`super().__init__(...)` は constructor initializer `: base(...)` へ lower する対応を追加した。
- 2026-03-01: `py_assert_stdout` / `py_assert_eq` / `py_assert_true` / `py_assert_all` の C# 側最小マッピングを追加し、fixture compile blocker を解消した。
- 2026-03-01: `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v` は pass（46 tests, 0 fail）。
- 2026-03-01: `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets cs --ignore-unstable-stdout` は pass（1/1）。
