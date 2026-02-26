# TASK GROUP: TG-P0-CPP-EAST2-REMOVAL

最終更新: 2026-02-24

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-CPP-EAST2-01` 〜 `P0-CPP-EAST2-01-S4`

背景:
- `py2cpp.py` は EAST3 既定化後も `--east-stage 2` 互換経路を残しており、分岐と互換処理が肥大化要因の1つになっている。
- 現在の運用方針では C++ 生成に `EAST2 -> C++` 経路は不要であり、保守コストだけが残る。
- ユーザー指示として「EAST2 -> C++ 変換を完全廃止し、最優先で扱う」が確定している。

目的:
- `py2cpp` の C++ 生成経路から `EAST2 -> C++` 互換処理を撤去し、EAST3 専用経路に一本化する。

対象:
- `src/py2cpp.py` の CLI/API にある `--east-stage 2` 受理経路と互換分岐。
- EAST2 互換ノード（For/ForRange 互換、legacy fallback など）を前提にした C++ 側の変換分岐。
- 関連テスト・検証スクリプト・ドキュメント。

非対象:
- Rust/JS/TS/Go/Java/Kotlin/Swift など他言語の `EAST2` 互換運用。
- EAST3 自体の仕様拡張。

受け入れ基準:
- `py2cpp` は `EAST3` のみを正規入力として扱い、`--east-stage 2` は明確なエラーになる。
- `EAST2 -> C++` 専用の互換分岐が削除され、不要な warning/compat コードが残らない。
- `py2cpp` 関連 test/check が EAST3 専用前提へ更新される。
- 仕様書（`spec-east`/`spec-dev` 等）に C++ 経路の EAST3 専用化が反映される。

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_noncpp_east3_contract.py`
- `python3 -m unittest test.unit.test_py2cpp_smoke`
- `python3 tools/check_todo_priority.py`

決定ログ:
- 2026-02-24: ユーザー指示により、`EAST2 -> C++` の互換経路を「最優先で完全廃止」する方針を確定。
- 2026-02-24: [ID: `P0-CPP-EAST2-01-S1`] `src/py2cpp.py` の `--east-stage 2` 受理を廃止し、`EAST2` 指定時はエラー停止へ変更。`load_east()` も `EAST3` 以外を拒否する契約に更新し、`test_py2cpp_features` / `test_east3_cpp_bridge` に拒否テストを追加した。
- 2026-02-24: [ID: `P0-CPP-EAST2-01-S2`] `src/py2cpp.py` の legacy 互換分岐を段階縮退。`BuiltinCall` の `runtime_call` 未指定 fallback（`bytes/bytearray` の self-hosted 互換）を撤去し、未 lower `type_id` Name-call を常時エラー化。未 lower builtin method fallback も撤去し、`check_py2cpp_transpile.py` は `checked=131 ok=131 fail=0 skipped=6` を維持した。
- 2026-02-24: [ID: `P0-CPP-EAST2-01-S3`] 回帰ガードを追加。`tools/check_py2cpp_transpile.py` で `--east-stage 2` が必ず失敗し、所定エラーメッセージを返すことを検査するように更新。`test/unit/test_py2cpp_smoke.py` を新設し、既定実行で互換警告が出ないことと `--east-stage 2` が拒否されることを固定した。`run_local_ci.py` に smoke を組み込んだ。
- 2026-02-24: [ID: `P0-CPP-EAST2-01-S4`] `docs-ja/spec/spec-east.md` / `docs-ja/spec/spec-dev.md` を同期し、`py2cpp.py` は `--east-stage 3` 専用、非 C++ 8変換器のみ `--east-stage 2` 互換モードを維持する現行仕様へ更新。
