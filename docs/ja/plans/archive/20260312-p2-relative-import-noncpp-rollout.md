<a href="../../../en/plans/archive/20260312-p2-relative-import-noncpp-rollout.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: relative import non-C++ rollout staging

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-RELATIVE-IMPORT-NONCPP-ROLLOUT-01`

背景:
- relative import の current coverage baseline は `cpp=build_run_locked`、それ以外は `not_locked` として inventory 化済み。
- ただし、次にどの backend から representative smoke を広げるか、どこまでを first wave とするか、未対応 lane をどう fail-closed に保つかがまだ live plan として固定されていない。
- current support claim を増やさずに rollout を進めるには、まず non-C++ 側の staged order と verification lane を決める必要がある。

目的:
- relative import の non-C++ rollout 順を first wave / second wave / long-tail に分けて固定する。
- first wave backend に対して、次に追加すべき representative smoke / fail-closed regression の粒度を決める。

対象:
- non-C++ backend rollout order の決定
- first wave backend と representative verification lane の決定
- fail-closed policy の handoff 明記

非対象:
- Rust / C# / 他 backend の relative import 実装そのもの
- support matrix 上で supported claim を増やすこと
- import graph / CLI semantics の変更

受け入れ基準:
- first wave / second wave / long-tail の backend group が明文化されている。
- first wave backend について `transpile smoke` と `backend-specific fail-closed` のどちらを先に固定するかが決まっている。
- current `cpp=build_run_locked` baseline を崩さずに next rollout task へ handoff できる。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `git diff --check`

決定ログ:
- 2026-03-12: current coverage baseline を閉じたので、次段は non-C++ rollout 順と representative verification lane を staged plan として固定する。
- 2026-03-12: rollout order は `first wave=rs/cs`, `second wave=go/java/js/kotlin/scala/swift/nim/ts`, `long-tail=lua/php/ruby` に固定した。
- 2026-03-12: first wave は `rs/cs` の `transpile smoke` を次 lane とし、support claim を広げる前提として `backend_specific_fail_closed` を全 non-C++ backend に維持する方針を inventory/checker で固定した。
- 2026-03-12: current coverage inventory と backend parity docs の双方から本 plan へ辿れる handoff link を追加し、next rollout の canonical docs path を固定した。

handoff 参照:
- coverage inventory: [relative_import_backend_coverage.py](/workspace/Pytra/src/toolchain/compiler/relative_import_backend_coverage.py)
- coverage checker: [check_relative_import_backend_coverage.py](/workspace/Pytra/tools/check_relative_import_backend_coverage.py)
- backend parity docs: [backend-parity-matrix.md](../language/backend-parity-matrix.md)

## 分解

- [x] [ID: P2-RELATIVE-IMPORT-NONCPP-ROLLOUT-01-S1-01] live plan / TODO を起票し、first wave / second wave / long-tail の rollout order を固定する。
- [x] [ID: P2-RELATIVE-IMPORT-NONCPP-ROLLOUT-01-S2-01] first wave backend の representative verification lane を `transpile smoke` / `fail-closed` に分けて固定する。
- [x] [ID: P2-RELATIVE-IMPORT-NONCPP-ROLLOUT-01-S2-02] current coverage inventory / backend parity docs から next rollout handoff へのリンクを同期する。
