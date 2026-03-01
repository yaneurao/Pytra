# P0: Kotlin 継承メソッド動的ディスパッチ改善

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-KOTLIN`

背景:
- Kotlin emitter は `open class` を出力するが、メソッドの `open/override` と `super` lower が不足している。

目的:
- Kotlin で継承メソッド動的ディスパッチを正しく成立させる。

対象:
- `src/hooks/kotlin/emitter/kotlin_native_emitter.py`

非対象:
- Kotlin backend 全体最適化

受け入れ基準:
- 基底メソッド `open`、派生メソッド `override` が出力される。
- `super` 呼び出しが no-op ではなく有効な呼び出しへ lower される。
- fixture parity が一致。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2kotlin_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets kotlin`

分解:
- [x] override 関係解析を追加して宣言キーワードを整備する。
- [x] `super` lower を実装する。
- [x] fixture 回帰を追加する。

決定ログ:
- 2026-03-01: Kotlin は `open/override` 導入を先行課題として確定した。
- 2026-03-01: クラス継承マップとメソッド集合を前処理で収集し、基底に同名メソッドがある場合は `override fun`、それ以外は `open fun` を出力するよう更新した。
- 2026-03-01: `super().method(...)` を Kotlin の `super.method(...)` へ lower し、`super` 式構文エラーを解消した。
- 2026-03-01: `test_py2kotlin_smoke.py` に継承 dispatch 回帰を追加し、`runtime_parity_check --targets kotlin`（1/1 pass）で fixture 一致を確認した。
