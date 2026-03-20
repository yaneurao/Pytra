# P0: C++ backend ディレクトリ再整列（5フォルダ -> `lower/optimizer/emitter`）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-DIR-REALIGN-01`

背景:
- `src/toolchain/emit/cpp/` 直下には `hooks/`, `header/`, `multifile/`, `profile/`, `runtime_emit/` が残っており、責務境界（`lower/optimizer/emitter`）と一致していない。
- 現在の 5 フォルダは主に `py2cpp.py` と `emitter` から参照されており、`lower`/`optimizer` と共通で使う部品ではない。
- 構成が混在したままだと、C++ backend の責務追跡・移行判断・selfhost 導線の保守コストが上がる。

目的:
- `src/toolchain/emit/cpp/` の実装境界を `lower/optimizer/emitter` 中心に再整列し、ルート直下の補助フォルダを撤去する。
- 5 フォルダ由来の機能を責務に合わせて `emitter` 配下へ集約し、`py2cpp.py` からの import 面を単純化する。

対象:
- `src/toolchain/emit/cpp/hooks/*`
- `src/toolchain/emit/cpp/header/*`
- `src/toolchain/emit/cpp/multifile/*`
- `src/toolchain/emit/cpp/profile/*`
- `src/toolchain/emit/cpp/runtime_emit/*`
- `src/toolchain/emit/cpp/emitter/*`（受け皿追加）
- `src/py2cpp.py`（import / 呼び出し先更新）
- 関連 unit test / check scripts

非対象:
- C++ 以外 backend の同時再編
- EAST3 / C++ IR 仕様そのものの変更
- `src/profiles/cpp/*.json` の配置変更

受け入れ基準:
- `src/toolchain/emit/cpp/` 直下に `hooks/`, `header/`, `multifile/`, `profile/`, `runtime_emit/` が存在しない。
- 旧 import（`toolchain.emit.cpp.hooks|header|multifile|profile|runtime_emit`）が production code から消える。
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

- [x] [ID: P0-CPP-DIR-REALIGN-01-S1-01] 現行 5 フォルダの責務と参照元（`py2cpp`/`emitter`/tests）を棚卸しし、移設先を確定する。
- [x] [ID: P0-CPP-DIR-REALIGN-01-S1-02] 新ディレクトリ方針（`emitter` 配下の受け皿名）を決定し、命名規約を文書化する。
- [x] [ID: P0-CPP-DIR-REALIGN-01-S2-01] `profile` を `emitter` 配下へ移設し、`py2cpp`/`CppEmitter` の import を更新する。
- [x] [ID: P0-CPP-DIR-REALIGN-01-S2-02] `hooks` を `emitter` 配下へ移設し、hook factory の呼び出し元を更新する。
- [x] [ID: P0-CPP-DIR-REALIGN-01-S2-03] `runtime_emit` を `emitter` 配下へ移設し、module include/runtime path 解決を更新する。
- [x] [ID: P0-CPP-DIR-REALIGN-01-S2-04] `header` を `emitter` 配下へ移設し、header 生成導線を更新する。
- [x] [ID: P0-CPP-DIR-REALIGN-01-S2-05] `multifile` を `emitter` 配下へ移設し、multi-file 出力導線を更新する。
- [x] [ID: P0-CPP-DIR-REALIGN-01-S2-06] 旧 5 フォルダを削除し、`toolchain.emit.cpp.*` import を新パスへ統一する。
- [x] [ID: P0-CPP-DIR-REALIGN-01-S3-01] 旧 import 再発防止の回帰テスト/検査（`rg` ベース or unit）を追加する。
- [x] [ID: P0-CPP-DIR-REALIGN-01-S3-02] unit/transpile/sample 回帰を実行し、非退行を確認して完了条件を満たす。

## S1-01 棚卸し結果（2026-03-02）

| 現行フォルダ | 主責務 | 主参照元 | 移設先（確定） |
| --- | --- | --- | --- |
| `toolchain/emit/cpp/profile/` | C++ profile loader / operator map / hooks loader | `src/py2cpp.py`, `toolchain/emit/cpp/emitter/*` | `toolchain/emit/cpp/emitter/profile_loader.py` |
| `toolchain/emit/cpp/hooks/` | C++ emitter hook registry（`build_cpp_hooks`） | `toolchain/emit/cpp/profile/cpp_profile.py`, `src/py2cpp.py`, test | `toolchain/emit/cpp/emitter/hooks_registry.py` |
| `toolchain/emit/cpp/runtime_emit/` | runtime path / include / namespace 解決 | `src/py2cpp.py`, `toolchain/emit/cpp/emitter/module.py` | `toolchain/emit/cpp/emitter/runtime_paths.py` |
| `toolchain/emit/cpp/header/` | EAST -> C++ header 生成 | `src/py2cpp.py` | `toolchain/emit/cpp/emitter/header_builder.py` |
| `toolchain/emit/cpp/multifile/` | multi-file 出力オーケストレーション | `src/py2cpp.py` | `toolchain/emit/cpp/emitter/multifile_writer.py` |

補足:
- 5 フォルダはいずれも `lower`/`optimizer` 共有部品ではなく、`emitter` 周辺または CLI bridge 向け補助であることを確認した。
- したがって本タスクでは、`lower/optimizer` 配下へは移さず `emitter` 配下へ集約する。

## S1-02 命名・import 規約（2026-03-02）

- `src/toolchain/emit/cpp/` 直下の正本ディレクトリは `lower/`, `optimizer/`, `emitter/` の3つに限定する。
- 補助モジュールは `emitter/` 直下に以下で配置する:
  - `profile_loader.py`
  - `hooks_registry.py`
  - `runtime_paths.py`
  - `header_builder.py`
  - `multifile_writer.py`
- 旧 import（`toolchain.emit.cpp.{profile,hooks,runtime_emit,header,multifile}`）は段階移行後に禁止する。
- `py2cpp.py` は backend helper を `toolchain.emit.cpp.emitter.*` からのみ import する。
- 後方互換 alias は移行期間のみ許容し、`S2-06` 完了時に削除する。

決定ログ:
- 2026-03-02: ユーザー指示により、`src/toolchain/emit/cpp/` 直下に残る 5 フォルダ（`hooks/header/multifile/profile/runtime_emit`）の整理を P0 として起票。
- 2026-03-02: 本タスクでは 5 フォルダを `lower/optimizer/emitter` のいずれかへ再配置する方針を採用し、共通部品扱いはしない前提を確定。
- 2026-03-02: [ID: P0-CPP-DIR-REALIGN-01-S1-01] 5 フォルダの責務/参照元を棚卸しし、移設先を `emitter` 配下5モジュールへ確定した。
- 2026-03-02: [ID: P0-CPP-DIR-REALIGN-01-S1-02] 命名規約と import 境界（`toolchain.emit.cpp.emitter.*` へ統一）を明文化した。
- 2026-03-02: [ID: P0-CPP-DIR-REALIGN-01-S2-01] `src/toolchain/emit/cpp/profile/cpp_profile.py` を `src/toolchain/emit/cpp/emitter/profile_loader.py` へ移設し、`py2cpp`/`CppEmitter`/関連 helper の import を新パスへ更新。`check_py2cpp_transpile.py` と `test_language_profile.py` で非退行を確認。
- 2026-03-02: [ID: P0-CPP-DIR-REALIGN-01-S2-02] `src/toolchain/emit/cpp/hooks/cpp_hooks.py` を `src/toolchain/emit/cpp/emitter/hooks_registry.py` へ移設し、`py2cpp`・profile loader・`profiles/cpp/profile.json` の hook factory 参照を更新。`test_cpp_hooks.py` と `check_py2cpp_transpile.py` で非退行を確認。
- 2026-03-02: [ID: P0-CPP-DIR-REALIGN-01-S2-03] `src/toolchain/emit/cpp/runtime_emit/cpp_runtime_emit.py` を `src/toolchain/emit/cpp/emitter/runtime_paths.py` へ移設し、`py2cpp`/`CppModuleEmitter` の runtime path 解決 import を新パスへ更新。`test_py2cpp_features.py -k runtime_module_tail_and_namespace_support_compiler_tree` と `check_py2cpp_transpile.py` で非退行を確認。
- 2026-03-03: [ID: P0-CPP-DIR-REALIGN-01-S2-04] `src/toolchain/emit/cpp/header/cpp_header.py` を `src/toolchain/emit/cpp/emitter/header_builder.py` へ移設し、`py2cpp` の import を新パスへ更新。
- 2026-03-03: [ID: P0-CPP-DIR-REALIGN-01-S2-05] `src/toolchain/emit/cpp/multifile/cpp_multifile.py` を `src/toolchain/emit/cpp/emitter/multifile_writer.py` へ移設し、multi-file 出力導線 import を新パスへ更新。
- 2026-03-03: [ID: P0-CPP-DIR-REALIGN-01-S2-06] `src/toolchain/emit/cpp/{hooks,header,multifile,profile,runtime_emit}` の Python 実体を削除し、旧 import 参照を撤去。
- 2026-03-03: [ID: P0-CPP-DIR-REALIGN-01-S3-01] `tools/check_cpp_backend_layout.py` を追加し、旧5フォルダ残存と旧 import の再発を fail-closed で検査可能にした。
- 2026-03-03: [ID: P0-CPP-DIR-REALIGN-01-S3-02] `check_cpp_backend_layout.py` / `check_py2cpp_boundary.py` / `check_py2cpp_transpile.py` / `sample/py/01 -> py2cpp` を実行し、移設範囲の非退行を確認。
