# P0: Rust 継承メソッド動的ディスパッチ改善

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-RS`

背景:
- Rust backend は `struct + impl` 中心で、Python 継承/`super` の直接対応が不足している。

目的:
- 継承メソッド呼び出し要件を満たす Rust 低減方式（trait/enum/composition）を確定する。

対象:
- `src/hooks/rs/emitter/rs_emitter.py`
- 必要時 `src/runtime/rs/pytra/py_runtime.rs`

非対象:
- Rust backend の所有権最適化全般

受け入れ基準:
- 継承メソッド dispatch の方針が実装可能形で固定される。
- fixture で期待出力が一致する。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rs_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets rs`

分解:
- [ ] Rust での継承エミュレーション方式を 1 つに絞る。
- [ ] `super` 相当呼び出しを lower する。
- [ ] fixture 回帰を追加する。

決定ログ:
- 2026-03-01: Rust は設計選択肢が複数あるため先に方式確定を置いた。
