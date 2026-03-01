# P0: Java 継承メソッド動的ディスパッチ改善

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-JAVA`

背景:
- Java は `extends` と仮想メソッドの土台があるが、`super()` lower や回帰固定が不足している。

目的:
- fixture で要求される `super()` + 基底参照経由呼び出しを安定して通す。

対象:
- `src/hooks/java/emitter/java_native_emitter.py`

非対象:
- Java backend の最適化一般

受け入れ基準:
- `super().__init__` / `super().method` lower が一貫して有効。
- fixture parity が一致。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2java_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets java`

分解:
- [x] `super` lower 条件を整理し、`__init__` 以外のメソッド経路も検証する。
- [x] fixture 断片の回帰テストを追加する。
- [x] parity で期待出力一致を確認する。

決定ログ:
- 2026-03-01: Java は既存基盤を利用しつつ回帰固定を強化する方針とした。
- 2026-03-01: `super().method(...)` が `super().method(...)` のまま出力され Java コンパイルエラーになる不具合を確認し、`super.method(...)` へ lower するよう修正した。
- 2026-03-01: `test_py2java_smoke.py` に `inheritance_virtual_dispatch_multilang` 向け回帰テストを追加し、`super.speak()` 出力を固定した。
- 2026-03-01: `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2java_smoke.py' -v`（23 tests, pass）と `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets java --ignore-unstable-stdout`（1/1 pass）を確認した。
