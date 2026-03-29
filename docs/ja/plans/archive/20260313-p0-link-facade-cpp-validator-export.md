<a href="../../../en/plans/archive/20260313-p0-link-facade-cpp-validator-export.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `toolchain.link` facade に C++ backend validator helper を昇格する

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-LINK-FACADE-CPP-VALIDATOR-EXPORT-01`

背景:
- 現在の `toolchain.link` package facade は link loader / manifest / optimizer の主要 API は再 export しているが、C++ backend 固有の validator helper である `validate_cpp_backend_input_doc()` と `translate_cpp_backend_emit_error()` は facade に載っていない。
- そのため `src/toolchain/compiler/typed_boundary.py` と一部 test は `toolchain.link.program_validator` へ直接 reach-through import している。
- validator helper 自体は link package の canonical validation seam なので、public facade と実利用 import path がずれたままだと package boundary の意味が薄く、後続 refactor 時にも submodule 固定依存が残る。

目的:
- `toolchain.link` facade に C++ backend validator helper 2 本を正規 export する。
- `typed_boundary` と representative link test を facade 経由の import に揃える。
- source contract を追加し、今後また submodule reach-through へ戻ったら fail-fast にする。

対象:
- `src/toolchain/link/__init__.py`
- `src/toolchain/compiler/typed_boundary.py`
- `tools/unittest/link/test_program_loader.py`
- 必要なら `tools/unittest/common/test_py2x_entrypoints_contract.py`

非対象:
- validator 実装そのものの仕様変更
- non-C++ backend 専用 helper の一括 facade export
- `toolchain.link.program_validator` module の分割や再配置

受け入れ基準:
- `from toolchain.link import validate_cpp_backend_input_doc` と `translate_cpp_backend_emit_error` が有効になる。
- `typed_boundary.py` が `toolchain.link.program_validator` 直接 import をやめる。
- representative link test / source contract が green になる。

確認コマンド:
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 -m unittest discover -s /workspace/Pytra/tools/unittest/link -p 'test_program_loader.py'`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 -m unittest discover -s /workspace/Pytra/tools/unittest/common -p 'test_py2x_entrypoints_contract.py'`
- `python3 /workspace/Pytra/tools/check/check_todo_priority.py`
- `git -C /workspace/Pytra diff --check`

分解:
- [x] [ID: P0-LINK-FACADE-CPP-VALIDATOR-EXPORT-01] `toolchain.link` package facade から `validate_cpp_backend_input_doc()` と `translate_cpp_backend_emit_error()` を正規 export し、`typed_boundary` / link test が submodule reach-through に依存しない状態へ揃える。
- [x] [ID: P0-LINK-FACADE-CPP-VALIDATOR-EXPORT-01-S1-01] facade export を要求する focused regression / source contract を追加し、current package-surface gap を fail-fast に固定する。
- [x] [ID: P0-LINK-FACADE-CPP-VALIDATOR-EXPORT-01-S2-01] `toolchain.link.__init__` export と `typed_boundary` / link test import を facade 経由へ切り替え、targeted unit を green に戻す。
- [x] [ID: P0-LINK-FACADE-CPP-VALIDATOR-EXPORT-01-S3-01] TODO / plan / decision log を同期して close 条件を固める。

決定ログ:
- 2026-03-13: TODO 空き後の follow-up P0 として、link package facade と実利用 import path のねじれを縮める task を起票した。対象は C++ backend validator helper 2 本に限定し、validator behavior 自体は変えない。
- 2026-03-13: `S1-01/S2-01` では facade export の runtime regression を `test_program_loader.py` に、source contract を `test_py2x_entrypoints_contract.py` に置いた。実装は `toolchain.link.__init__` の再 export と `typed_boundary` import path の切替に限定し、`program_validator.py` の behavior には触れていない。
- 2026-03-13: `S3-01` では active TODO / plan / archive を同期し、close 条件を「`toolchain.link` facade export、`typed_boundary` facade import、runtime regression と source contract が両方 green」に固定した。追加の export 拡大は次 task へ回す。
