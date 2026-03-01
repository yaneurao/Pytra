# P0: JavaScript 継承メソッド動的ディスパッチ改善

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-JS`

背景:
- JS emitter は class を出すが `extends`/`super` 経路が不足し、Python 継承意味論から乖離している。

目的:
- JS 出力を `class Child extends Base` + `super(...)` ベースへ整理する。

対象:
- `src/hooks/js/emitter/js_emitter.py`

非対象:
- TS 側の型注釈拡張

受け入れ基準:
- 継承クラスで `extends` を出力する。
- `super().__init__` / `super().method` lower が成立する。
- fixture parity が一致。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2js_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets js`

分解:
- [ ] class 宣言に `extends` を導入する。
- [ ] `super` 呼び出し lower を追加する。
- [ ] fixture 回帰を追加する。

決定ログ:
- 2026-03-01: JS は class 表現の根幹を優先して修正する。
