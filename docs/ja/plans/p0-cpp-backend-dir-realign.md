# P0: C++ backend ディレクトリ再整列（5フォルダ -> `lower/optimizer/emitter`）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-DIR-REALIGN-01`

背景:
- `src/backends/cpp/` 直下には `hooks/`, `header/`, `multifile/`, `profile/`, `runtime_emit/` が残っており、責務境界（`lower/optimizer/emitter`）と一致していない。
- 現在の 5 フォルダは主に `py2cpp.py` と `emitter` から参照されており、`lower`/`optimizer` と共通で使う部品ではない。
- 構成が混在したままだと、C++ backend の責務追跡・移行判断・selfhost 導線の保守コストが上がる。

目的:
- `src/backends/cpp/` の実装境界を `lower/optimizer/emitter` 中心に再整列し、ルート直下の補助フォルダを撤去する。
- 5 フォルダ由来の機能を責務に合わせて `emitter` 配下へ集約し、`py2cpp.py` からの import 面を単純化する。

対象:
- `src/backends/cpp/hooks/*`
- `src/backends/cpp/header/*`
- `src/backends/cpp/multifile/*`
- `src/backends/cpp/profile/*`
- `src/backends/cpp/runtime_emit/*`
- `src/backends/cpp/emitter/*`（受け皿追加）
- `src/py2cpp.py`（import / 呼び出し先更新）
- 関連 unit test / check scripts

非対象:
- C++ 以外 backend の同時再編
- EAST3 / C++ IR 仕様そのものの変更
- `src/profiles/cpp/*.json` の配置変更

受け入れ基準:
- `src/backends/cpp/` 直下に `hooks/`, `header/`, `multifile/`, `profile/`, `runtime_emit/` が存在しない。
- 旧 import（`backends.cpp.hooks|header|multifile|profile|runtime_emit`）が production code から消える。
- `py2cpp.py` の主要導線（single-file / multi-file / emit-runtime-cpp）が非退行で動作する。
- C++ 回帰（unit + transpile check + sample regeneration）が通る。

実施方針:
1. 5 フォルダの責務を再分類し、`emitter` 配下の新規モジュールへ移設する。
2. 参照元 import を新パスへ一括更新し、旧パッケージを段階的に削除する。
3. 旧 import 再発を検知するガード（unit or check script）を追加する。
4. 回帰テストと sample 再生成で非退行を確認する。

配置方針（案）:
- `hooks/` -> `emitter/hooks_registry.py`
- `profile/` -> `emitter/profile_loader.py`
- `runtime_emit/` -> `emitter/runtime_paths.py`
- `header/` -> `emitter/header_builder.py`
- `multifile/` -> `emitter/multifile_writer.py`

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_cpp_*' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --force`

## 分解

- [ ] [ID: P0-CPP-DIR-REALIGN-01-S1-01] 現行 5 フォルダの責務と参照元（`py2cpp`/`emitter`/tests）を棚卸しし、移設先を確定する。
- [ ] [ID: P0-CPP-DIR-REALIGN-01-S1-02] 新ディレクトリ方針（`emitter` 配下の受け皿名）を決定し、命名規約を文書化する。
- [ ] [ID: P0-CPP-DIR-REALIGN-01-S2-01] `profile` を `emitter` 配下へ移設し、`py2cpp`/`CppEmitter` の import を更新する。
- [ ] [ID: P0-CPP-DIR-REALIGN-01-S2-02] `hooks` を `emitter` 配下へ移設し、hook factory の呼び出し元を更新する。
- [ ] [ID: P0-CPP-DIR-REALIGN-01-S2-03] `runtime_emit` を `emitter` 配下へ移設し、module include/runtime path 解決を更新する。
- [ ] [ID: P0-CPP-DIR-REALIGN-01-S2-04] `header` を `emitter` 配下へ移設し、header 生成導線を更新する。
- [ ] [ID: P0-CPP-DIR-REALIGN-01-S2-05] `multifile` を `emitter` 配下へ移設し、multi-file 出力導線を更新する。
- [ ] [ID: P0-CPP-DIR-REALIGN-01-S2-06] 旧 5 フォルダを削除し、`backends.cpp.*` import を新パスへ統一する。
- [ ] [ID: P0-CPP-DIR-REALIGN-01-S3-01] 旧 import 再発防止の回帰テスト/検査（`rg` ベース or unit）を追加する。
- [ ] [ID: P0-CPP-DIR-REALIGN-01-S3-02] unit/transpile/sample 回帰を実行し、非退行を確認して完了条件を満たす。

決定ログ:
- 2026-03-02: ユーザー指示により、`src/backends/cpp/` 直下に残る 5 フォルダ（`hooks/header/multifile/profile/runtime_emit`）の整理を P0 として起票。
- 2026-03-02: 本タスクでは 5 フォルダを `lower/optimizer/emitter` のいずれかへ再配置する方針を採用し、共通部品扱いはしない前提を確定。
