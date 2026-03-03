# P1: `py2x.py` 単一エントリ化（`py2*.py` 廃止、最終的に `py2cpp.py` 削除）

最終更新: 2026-03-03

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-PY2X-SINGLE-ENTRY-01`

背景:
- 現在は `py2x.py` を導入済みだが、`tools/` / `test/` / `docs/` / selfhost 導線が依然として `py2*.py` 直呼び出しに依存している。
- 特に `py2cpp.py` は `--emit-runtime-cpp` / `--header-output` / `--multi-file` など C++ 固有機能の入口を兼ねており、単純削除できない。
- ユーザー要件は「`py2x.py` に統一したなら legacy CLI を不要化し、最終的に `py2cpp.py` を無くす」ことである。

目的:
- CLI の正規入口を `src/py2x.py`（通常）と `src/py2x-selfhost.py`（selfhost）に統一する。
- `py2*.py` 直依存を `tools/` / `test/` / `docs/` から段階的に除去する。
- 最終段階で `src/py2cpp.py` を含む legacy CLI を削除する。

対象:
- `src/py2x.py` / `src/py2x-selfhost.py` の機能拡張（C++ 専用機能吸収）
- `tools/` / `test/` / `src/pytra/cli.py` の呼び出し先を `py2x.py --target ...` へ移行
- selfhost 関連スクリプトの entrypoint 置換
- `docs/ja` / `docs/en` の利用手順更新
- legacy CLI（`src/py2*.py`）削除

非対象:
- backend 変換ロジック自体の品質改善
- EAST 仕様変更
- runtime API 仕様変更

受け入れ基準:
- `tools/`, `test/`, `docs/`, `src/pytra/cli.py` に `src/py2*.py` 直参照が残らない。
- C++ 専用運用（runtime 生成・header 出力・multi-file）が `py2x --target cpp` で代替可能。
- selfhost 導線が `py2cpp.py` 非依存で成立する。
- 最終状態で `src/py2cpp.py` が削除され、主要回帰が通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `rg -n "src/py2(?!x)\\w*\\.py" src tools test docs`
- `python3 tools/check_py2x_transpile.py`（新設予定）
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2cs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2php_transpile.py`
- `python3 tools/check_py2nim_transpile.py`
- `python3 tools/build_selfhost.py`
- `python3 tools/build_selfhost_stage2.py`

## 分解

- [ ] [ID: P1-PY2X-SINGLE-ENTRY-01-S1-01] `tools/` / `test/` / `docs/` / `src/pytra/cli.py` の `py2*.py` 依存箇所を棚卸しし、移行順序を確定する。
- [ ] [ID: P1-PY2X-SINGLE-ENTRY-01-S1-02] `py2cpp.py` 固有機能（`--emit-runtime-cpp`, `--header-output`, `--multi-file` 等）の `py2x` 受け皿仕様を確定する。
- [ ] [ID: P1-PY2X-SINGLE-ENTRY-01-S1-03] selfhost 導線（prepare/build/check）がどの entrypoint 契約に依存しているかを棚卸しし、置換方針を確定する。
- [ ] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-01] `py2x --target cpp` に `py2cpp` 固有機能を実装し、既存オプションと等価運用できるようにする。
- [ ] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-02] `tools/` の CLI 呼び出しを `py2x.py --target ...` へ一括置換する。
- [ ] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-03] `test/` の CLI 呼び出しと契約テストを `py2x` ベースへ移行する。
- [ ] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-04] `docs/ja` / `docs/en` の使用例と仕様表記を `py2x` 正規入口へ更新する。
- [ ] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] selfhost スクリプトを `py2cpp.py` 非依存へ移行し、`py2x-selfhost.py` 基準で再配線する。
- [ ] [ID: P1-PY2X-SINGLE-ENTRY-01-S3-01] legacy CLI 撤去前のガードを追加し、`py2*.py` 新規再流入を fail-fast で検出する。
- [ ] [ID: P1-PY2X-SINGLE-ENTRY-01-S3-02] `src/py2cpp.py` を削除し、必要に応じて他 `py2*.py` も同時撤去する。
- [ ] [ID: P1-PY2X-SINGLE-ENTRY-01-S3-03] 全 transpile/selfhost 回帰を実行し、`py2cpp.py` 削除後の非退行を確認する。

決定ログ:
- 2026-03-03: ユーザー指示により、`py2x.py` 単一エントリ化を P1 として起票し、最終成果に `src/py2cpp.py` 削除を含める方針を確定。
