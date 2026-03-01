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
- [ ] call lower に `super` 専用分岐を追加する。
- [ ] `initialize` 系の引数転送を検証する。
- [ ] fixture 回帰を追加する。

決定ログ:
- 2026-03-01: Ruby は `super` lower 欠落を第一優先で補完する方針とした。
