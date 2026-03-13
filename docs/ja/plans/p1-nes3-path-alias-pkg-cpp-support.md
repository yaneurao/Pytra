# P1: `pytra.std.pathlib.Path` の別モジュール alias 再利用を C++ multi-file contract に揃える

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-NES3-PATH-ALIAS-PKG-CPP-01`

背景:
- Pytra-NES3 repro [`materials/refs/from-Pytra-NES3/path_alias_pkg/`](../../../materials/refs/from-Pytra-NES3/path_alias_pkg) は `.compat` モジュールが再公開した `Path` を `.entry` 側で再利用する。
- 2026-03-13 時点の generated C++ では `compat.h` が `make_path` しか宣言せず、`entry.cpp` は存在しない `pytra_mod_compat::Path(raw)` を呼んで compile failure になる。
- これは `Path` 自体の runtime 問題ではなく、別モジュール経由で再利用した alias/type symbol を value call として誤分類している残差である。

目的:
- `from .compat import Path` を C++ multi-file lane で type/alias として解決し、存在しない module function call へ lower しない。
- user module が再公開した std type symbol の representative reuse lane を focused contract として固定する。

対象:
- cross-module imported alias/type symbol の分類と C++ name rendering
- `materials/refs/from-Pytra-NES3/path_alias_pkg/` の multi-file compile smoke
- path alias residual の regression / docs / TODO 同期

非対象:
- `Path` runtime API の新機能追加
- 全 built-in 型 alias の一括 redesign
- non-C++ backend への横展開

受け入れ基準:
- `path_alias_pkg` の generated C++ が compile できる。
- consumer module が存在しない `pytra_mod_compat::Path(...)` を emit しない。
- user module 経由で再公開した `Path` の representative reuse lane が regression で固定される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `bash ./pytra materials/refs/from-Pytra-NES3/path_alias_pkg/entry.py --target cpp --output-dir /tmp/pytra_nes3_path_alias_pkg`
- `for f in /tmp/pytra_nes3_path_alias_pkg/src/*.cpp; do g++ -std=c++20 -O0 -c "$f" -I /tmp/pytra_nes3_path_alias_pkg/include -I /workspace/Pytra/src -I /workspace/Pytra/src/runtime/cpp; done`
- `git diff --check`

## 分解

- [ ] [ID: P1-NES3-PATH-ALIAS-PKG-CPP-01-S1-01] current compile failure と alias/type misclassification residual を focused regression / plan / TODO に固定する。
- [ ] [ID: P1-NES3-PATH-ALIAS-PKG-CPP-01-S2-01] cross-module `Path` alias を type/constructor lane として正しく解決するよう symbol classification / rendering を修正する。
- [ ] [ID: P1-NES3-PATH-ALIAS-PKG-CPP-01-S3-01] multi-file compile smoke と docs wording を current contract に同期する。

決定ログ:
- 2026-03-13: `Path` stringify ではなく cross-module alias reuse の問題なので、Pytra-NES3 repro 専用の separate task として起票する。
