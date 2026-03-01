# P0: TypeScript 継承メソッド動的ディスパッチ改善

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-TS`

背景:
- TS backend は現状 JS emitter 委譲のため、継承/`super` 品質が JS 側に依存している。

目的:
- TS 出力でも継承ディスパッチ要件を満たし、preview 依存を減らす。

対象:
- `src/hooks/ts/emitter/ts_emitter.py`
- 必要時 `src/hooks/js/emitter/js_emitter.py`

非対象:
- TS 完全 native emitter への全面移行

受け入れ基準:
- TS 出力で `extends` / `super` 経路が有効。
- fixture parity が一致。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2ts_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets ts`

分解:
- [x] JS 委譲経路で継承ディスパッチ要件を満たす最小修正を導入する。
- [x] TS 出力固有の破綻（構文/型）を回帰で固定する。
- [x] fixture parity を確認する。

決定ログ:
- 2026-03-01: TS は JS 修正に追従させつつ専用課題を切り出す方針とした。
- 2026-03-01: JS 側の `extends/super` 修正を取り込んだ状態で `test_py2ts_smoke.py`（15 tests）を実行し、回帰がないことを確認した。
- 2026-03-01: `runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets ts --ignore-unstable-stdout` を実行し、fixture parity（1/1 pass）を確認した。
