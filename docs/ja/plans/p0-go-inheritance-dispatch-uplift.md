# P0: Go 継承メソッド動的ディスパッチ改善

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-GO`

背景:
- Go backend は埋め込みで継承風構造を作るが、Python 互換の基底参照ディスパッチを保証できていない。

目的:
- 継承メソッド呼び出しで Python 相当の解決順序を維持できる lower 方式へ整理する。

対象:
- `src/hooks/go/emitter/go_native_emitter.py`
- 必要時 `src/runtime/go/pytra/py_runtime.go`

非対象:
- Go 言語仕様を超える多重継承

受け入れ基準:
- `super()` 相当の呼び出し経路が no-op でなく有効化される。
- fixture の期待出力を満たすコード生成ルールが確立される。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets go`

分解:
- [x] Go での継承表現（埋め込み/インターフェース）を比較し、採用方式を確定する。
- [x] `super()` lower と派生メソッド解決の規則を実装する。
- [x] fixture 回帰で非退行を固定する。

決定ログ:
- 2026-03-01: Go は設計差が大きいため独立 plan とした。
- 2026-03-01: 継承型注釈は `*Class` ではなく class interface（`AnimalLike` など）で受ける方式を採用し、基底参照経由の動的ディスパッチを成立させた。
- 2026-03-01: `super().method(...)` は埋め込み基底（`self.<Base>.method(...)`）へ lower、`super().__init__(...)` は `self.<Base>.Init(...)` へ lower する規則を実装した。
- 2026-03-01: `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go_smoke.py' -v` は pass（12 tests, 0 fail）。
- 2026-03-01: `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets go --ignore-unstable-stdout` は pass（1/1）。
