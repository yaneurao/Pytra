# P0: Ruby 継承メソッド動的ディスパッチ改善

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-RUBY`

背景:
- Ruby は継承自体は扱えるが、`super` 呼び出し lower が不足している。

目的:
- `super().__init__` / `super().method` を Ruby の `super` へ正しく lower する。

対象:
- `src/hooks/ruby/emitter/ruby_native_emitter.py`

非対象:
- Ruby runtime の性能最適化

受け入れ基準:
- `super` 呼び出しが Python 意味論に沿って出力される。
- fixture parity が一致。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets ruby`

分解:
- [x] call lower に `super` 専用分岐を追加する。
- [x] `initialize` 系の引数転送を検証する。
- [x] fixture 回帰を追加する。

決定ログ:
- 2026-03-01: Ruby は `super` lower 欠落を第一優先で補完する方針とした。
- 2026-03-01: `super().method` を `self.class.superclass.instance_method(:method).bind(self).call(...)` へ lower する分岐を追加し、`super_()` への誤変換を解消した。
- 2026-03-01: `py_assert_*` 呼び出しを `__pytra_assert()` へ縮退し、引数評価による `_case_main` 実行副作用を抑制した。
- 2026-03-01: `test_py2rb_smoke.py`（20 tests）と `runtime_parity_check --targets ruby`（1/1 pass）で継承 dispatch fixture の一致を確認した。
