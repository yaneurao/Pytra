<a href="../../../en/plans/archive/20260313-p0-cpp-backend-input-validator-itertree.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ backend input validator の object-tree iterator 追従漏れを解消する

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/archive/20260313.md` の `ID: P0-CPP-BACKEND-INPUT-VALIDATOR-ITERTREE-01`

背景:
- `src/toolchain/link/program_validator.py` の `_iter_object_tree()` は raw object tree 走査時に `parent_key` も返す API に拡張された。
- raw EAST3 validator 側はこの新 API へ追従済みだが、`validate_cpp_backend_input_doc()` は旧 2-value unpack のまま残っている。
- そのため、minimal valid module ですら C++ backend input validation に入った瞬間 `too many values to unpack` で止まり得る。これは `typed_boundary.py` が呼ぶ C++ backend carrier validation の足元でもあり、実際の backend emit error 変換まで到達しない。

目的:
- `validate_cpp_backend_input_doc()` を `_iter_object_tree()` の current API に追従させる。
- current crash surface を focused regression で固定し、今後 iterator signature が変わっても link-stage validator が fail-fast に検知できるようにする。
- 既存の `ForCore.iter_plan` metadata guard と error wording は維持する。

対象:
- `src/toolchain/link/program_validator.py`
- `tools/unittest/link/test_program_loader.py`
- TODO / plan の進捗同期

非対象:
- raw EAST3 validator 全体の再設計
- non-C++ backend input validation
- `ForCore` 自体の metadata 仕様変更

受け入れ基準:
- minimal valid raw EAST3 module を `validate_cpp_backend_input_doc()` へ渡しても tuple unpack error で落ちない。
- `validate_cpp_backend_input_doc()` は `_iter_object_tree()` からの `parent_key` を受け取っても既存の `ForCore` metadata validation を維持する。
- targeted link regression が green になる。

確認コマンド:
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 -m unittest discover -s /workspace/Pytra/tools/unittest/link -p 'test_program_loader.py'`
- `python3 /workspace/Pytra/tools/check/check_todo_priority.py`
- `git -C /workspace/Pytra diff --check`

分解:
- [x] [ID: P0-CPP-BACKEND-INPUT-VALIDATOR-ITERTREE-01] `validate_cpp_backend_input_doc()` を `_iter_object_tree()` の `parent_key` 付き API に追従させ、typed boundary / backend input validation が tuple unpack error で止まらない状態へ戻す。
- [x] [ID: P0-CPP-BACKEND-INPUT-VALIDATOR-ITERTREE-01-S1-01] minimal raw EAST3 module を使った focused regression を追加し、C++ backend input validator の current crash surface を fail-fast で固定する。
- [x] [ID: P0-CPP-BACKEND-INPUT-VALIDATOR-ITERTREE-01-S2-01] `validate_cpp_backend_input_doc()` を `parent_key` 付き object-tree iteration へ切り替え、既存 `ForCore` metadata guard を維持したまま targeted link test を green に戻す。
- [x] [ID: P0-CPP-BACKEND-INPUT-VALIDATOR-ITERTREE-01-S3-01] TODO / plan / decision log を同期して close 条件を固める。

決定ログ:
- 2026-03-13: TODO 空き後の新しい P0 として、既存の converter core 破綻を優先する。対象は `_iter_object_tree()` signature 変更に追従し忘れた `validate_cpp_backend_input_doc()` に限定し、raw EAST3 validator 全体の再設計へは広げない。
- 2026-03-13: `S1-01/S2-01` では link-stage focused regression を `test_program_loader.py` に置き、minimal `Module` input を `validate_cpp_backend_input_doc()` へ直渡しする形で crash surface を固定した。実装側は `_iter_object_tree()` から `parent_key` を受け取るだけに留め、`ForCore.iter_plan` validation と error wording は変えない。
- 2026-03-13: `S3-01` で live TODO / archive / archived plan を同期し、close 条件を「minimal `Module` input が tuple unpack error で止まらず、focused link regression と TODO priority check が green」で固定した。実装 commit は既存の `program_validator.py` fix をそのまま採用し、追加の validator behavior 変更は入れていない。
