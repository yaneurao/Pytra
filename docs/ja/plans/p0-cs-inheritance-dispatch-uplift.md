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
- [ ] 基底メソッドオーバーライド関係を事前解析し、メソッド宣言へ `virtual/override` を付与する。
- [ ] `super()` 呼び出しを `base` 呼び出しへ lower する。
- [ ] fixture の transpile + parity 回帰を追加する。

決定ログ:
- 2026-03-01: C# を最優先対象の一つとして独立 plan 化した。
