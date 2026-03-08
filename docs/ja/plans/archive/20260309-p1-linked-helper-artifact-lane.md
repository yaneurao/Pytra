# P1: linked-program optimizer から helper artifact を正規出力できるようにする

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-LINKED-HELPER-ARTIFACT-01`

関連:
- [20260307-p0-linked-program-global-optimizer-and-program-writer.md](./archive/20260307-p0-linked-program-global-optimizer-and-program-writer.md)
- [p2-runtime-sot-linked-program-integration.md](./p2-runtime-sot-linked-program-integration.md)

背景:
- 現状の linked-program optimizer は既存 module を最適化して metadata を付けるだけで、optimizer 自身が helper 関数や helper module を「別 artifact」として返す標準レーンを持っていない。
- 一方で C++ には既に [program_writer.py](../../../src/backends/cpp/program_writer.py) があり、複数 module artifact を別ファイルへ配置する場所自体は存在する。
- この中間レーンが欠けているため、intrinsic helper や lowering helper を optimizer / linker 段から正しく外出しできず、結果として [py_runtime.h](../../../src/runtime/cpp/native/core/py_runtime.h) や checked-in runtime、各 emitter の inline helper に処理を押し込む傾向が強くなる。
- single-file backend と multi-file backend で最終的な helper 配置は違ってよいが、少なくとも「helper artifact を program の一部として運ぶ」共通表現は必要である。

目的:
- linked-program optimizer / linker が synthetic helper module を first-class output として返せるようにする。
- backend は「通常 module + helper artifact」を同じ program artifact の一部として受け取れるようにする。
- multi-file backend は helper artifact を別ファイルとして配置でき、single-file backend は main artifact へ折り畳めるようにする。
- helper を事前に runtime へ押し込む設計を減らし、`py_runtime.h` 肥大化の原因を取り除く。

対象:
- linked-program model / schema / materializer
- linked-program optimizer 出力契約
- backend 共通 program artifact 契約
- `CodeEmitter` / backend registry / `ir2lang.py` の helper artifact 受け渡し
- C++ `ProgramWriter` における helper module の配置
- representative proof として 1 件の helper を synthetic helper module として流す経路

非対象:
- すべての helper を一度に runtime から追い出すこと
- `py_runtime.h` の全面解体
- runtime SoT 全体を linked-program ordinary module に統合すること
- 全 backend を同時に multi-file へ移行すること
- backend 固有 helper naming / namespace の最終決着

受け入れ基準:
- linked-program optimizer の出力に synthetic helper module を表す canonical lane が追加される。
- `link-output.json` と backend restart 導線が helper artifact を保持・再読込できる。
- backend 共通 program artifact に helper module を含められる。
- C++ multi-file 出力では helper artifact を別ファイルへ配置できる。
- single-file backend は helper artifact を main artifact へ折り畳める。
- representative case で、従来 `py_runtime.h` や emitter inline helper に置いていた処理を helper artifact へ逃がせることを確認する。
- debug/restart/sample parity で helper artifact 経路が非退行である。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit/link -p 'test_*.py' -v`
- `python3 -m unittest discover -s test/unit/tooling -p 'test_ir2lang_cli.py' -v`
- `python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_program_writer.py' -v`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

## 1. 問題の本質

今の欠陥は「別ファイルが出せない」ことではない。

- C++ には既に `ProgramWriter` がある。
- しかし linked-program optimizer は helper を新しい module/artifact として返せない。
- 共通 backend 契約も helper artifact を first-class に扱わない。

結果として helper の置き場所が

- runtime (`py_runtime.h`, checked-in runtime)
- emitter inline helper
- 手書き backend 専用 sugar

に偏る。  
つまり欠けているのは「ファイル出力先」ではなく、「optimizer-generated helper artifact の中間表現」である。

## 2. 目標アーキテクチャ

目標は次の流れである。

```text
EAST3 Module 群
  -> LinkedProgramLoader
  -> LinkedProgramOptimizer
       - 既存 module の最適化
       - synthetic helper module の生成
  -> link-output.json + linked modules + linked helper modules
  -> BackendLower / ModuleEmitter
  -> ProgramArtifact(modules=[user, runtime, helper])
  -> ProgramWriter
       - multi-file backend: helper を別ファイル化
       - single-file backend: helper を main artifact へ fold
```

重要なのは、helper artifact を

- backend 固有の ad-hoc inline helper

ではなく

- linked program から流れてくる canonical module artifact

として扱うことである。

## 3. canonical 中間表現

### 3.1 linked-program module kind

`LinkedProgramModule` に少なくとも次を追加する。

- `module_kind`
  - `user`
  - `runtime`
  - `helper`
- `generated_by`
  - `""` または `linked_optimizer`
- `owner_module_id`
  - helper の論理所有元 module
- `helper_id`
  - backend 共通の stable helper id

### 3.2 synthetic helper module の原則

- helper は `kind=Module` の IR を維持する。
- ただし `meta.synthetic_helper_v1` を必須にする。
- helper module 自身は user source path を持たず、`source_path=""` を canonical にする。
- helper の名前は stable で deterministic にする。

例:

```json
{
  "kind": "Module",
  "east_stage": 3,
  "module_id": "__pytra_helper__.cpp.intrinsic.list_at_boundscheck",
  "meta": {
    "synthetic_helper_v1": {
      "helper_id": "cpp.intrinsic.list_at_boundscheck",
      "owner_module_id": "app.main",
      "generated_by": "linked_optimizer"
    }
  }
}
```

## 4. link-output / restart 契約

`link-output.json` は helper artifact を落とさず保持する必要がある。

最低限:

- `modules[]` に helper module entry を含める
- `kind=helper`
- `helper_id`
- `owner_module_id`

backend-only restart (`ir2lang.py`) は

- 通常 module
- helper module

の両方を読む。  
これにより debug/restart 経路でも optimizer-generated helper を再現できる。

## 5. backend 契約

### 5.1 共通 program artifact

program artifact の `modules[]` は user/runtime/helper を区別できる必要がある。

最低限:

- `module_id`
- `label`
- `kind`
- `is_entry`
- `metadata`
- `text`

helper module には:

- `kind="helper"`
- `metadata.helper_id`
- `metadata.owner_module_id`

を付ける。

### 5.2 backend 側の責務

- `ModuleEmitter`
  - helper module も通常 module と同じく描画できる
- `ProgramWriter`
  - `kind=helper` を受け入れる
  - multi-file backend は helper を別ファイルへ置ける
  - single-file backend は helper text を main artifact へ fold できる

## 6. C++ first implementation

最初の proof は C++ で行う。

理由:

- multi-file `ProgramWriter` が既にある
- `py_runtime.h` へ helper を押し込みやすい問題が最も強い
- sample parity / fixture parity の guard が揃っている

### 6.1 first proof の条件

- helper artifact 1 件だけでよい
- runtime core を壊さない小さい helper を選ぶ
- `py_runtime.h` か emitter inline helper から 1 件移せれば十分

候補:

- bounds-check / temporary helper
- intrinsic lowering helper
- tiny adapter helper

## 7. single-file backend fallback

single-file backend では別ファイル化は必須ではない。

方針:

- helper artifact は canonical に生成する
- ただし `ProgramWriter` が fold して main file に畳む

これにより

- optimizer / linker / restart 契約は全 target 共通
- 配置だけ backend ごとに違う

という分離を保てる。

## 8. 実装フェーズ

### Phase 1: 契約固定

- schema / module kind / helper metadata を spec と plan に固定する
- helper artifact を `runtime helper` / `synthetic helper` / `inline helper` から区別する

### Phase 2: linked-program model 拡張

- `LinkedProgramModule` と `link-output.json` に helper lane を追加
- materializer / validator / loader を helper aware にする

### Phase 3: backend artifact 契約拡張

- common program artifact に `kind=helper` を追加
- `CodeEmitter` / backend registry / `ir2lang.py` を helper aware にする

### Phase 4: C++ proof

- 1 件の helper を synthetic helper module 化
- C++ `ProgramWriter` で別ファイルとして配置
- sample / fixture / restart で非退行確認

### Phase 5: single-file fallback

- representative single-file backend 1 件で fold 経路を確認
- helper artifact が inline helper に戻らずに流れることを確認

## 9. 分解

- `P1-LINKED-HELPER-ARTIFACT-01-S1-01`: 現状の helper 逃し先と blocker を棚卸しする。
- `P1-LINKED-HELPER-ARTIFACT-01-S1-02`: helper artifact schema / module kind / metadata 契約を spec に固定する。
- `P1-LINKED-HELPER-ARTIFACT-01-S2-01`: linked-program model / validator / materializer を helper-aware にする。
- `P1-LINKED-HELPER-ARTIFACT-01-S2-02`: `link-output.json` / restart 導線へ helper module lane を追加する。
- `P1-LINKED-HELPER-ARTIFACT-01-S3-01`: backend 共通 program artifact に `kind=helper` を追加する。
- `P1-LINKED-HELPER-ARTIFACT-01-S3-02`: `CodeEmitter` / `ir2lang.py` / backend registry を helper-aware にする。
- `P1-LINKED-HELPER-ARTIFACT-01-S4-01`: C++ proof helper を synthetic helper module として materialize する。
- `P1-LINKED-HELPER-ARTIFACT-01-S4-02`: C++ `ProgramWriter` で helper を別ファイル化し、fixture/sample parity を確認する。
- `P1-LINKED-HELPER-ARTIFACT-01-S5-01`: representative single-file backend で helper fold 経路を確認する。
- `P1-LINKED-HELPER-ARTIFACT-01-S5-02`: docs / guard / archive を更新する。

## 10. S1-01 棚卸し結果

### 10.1 helper の現状 escape hatch

- `py_runtime.h`
  - `src/runtime/cpp/native/core/py_runtime.h` は low-level core と helper convenience の両方を背負ってきた。
  - 2026-03-09 時点で object/dict convenience のかなりの tranche は削ったが、helper を runtime へ事前配置する圧力が残っている。
- checked-in/generated runtime module
  - `src/runtime/cpp/generated/**` と `src/runtime/cpp/native/**` は、本来 optimizer/generated helper artifact として外へ出したい処理の受け皿を兼ねている。
  - とくに `generated/built_in/*.h|cpp` は runtime helper と synthetic helper の境界が曖昧になりやすい。
- emitter 側の special-op include
  - `src/backends/cpp/emitter/module.py` の `_CPP_HELPER_INCLUDE_BY_SPECIAL_OP` は `RuntimeSpecialOp` / `PathRuntimeOp` を ad-hoc include へ解決している。
  - これは helper を「linked-program から届く artifact」ではなく「emitter が必要に応じて header を足すもの」として扱っていることを示す。
- emitter inline helper / backend-local sugar
  - `src/backends/cpp/emitter/runtime_expr.py`、`builtin_runtime.py`、`call.py`、`stmt.py` には backend-local lowering helper が残っている。
  - これらは IR の 1 node を local string helper で処理しており、optimizer-generated helper module を受け取る設計になっていない。

### 10.2 linked-program 側の blocker

- `LinkedProgramModule`
  - `src/toolchain/link/program_model.py` の `LinkedProgramModule` は `module_id/source_path/is_entry/east_doc/artifact_path` しか持たず、`module_kind`, `helper_id`, `owner_module_id` を表せない。
- `link-output.json`
  - `src/toolchain/link/global_optimizer.py` の `module_entries` は `module_id/input/output/source_path/is_entry` のみで、helper module を区別する lane が無い。
  - `_linked_output_path()` も常に `linked/<module>.east3.json` 固定で、helper 専用 prefix や metadata を持てない。
- materializer / restart
  - `src/toolchain/link/materializer.py` は `result.linked_program.modules` だけを書き出し、helper artifact 群を別 collection として持たない。
  - `load_linked_output_bundle()` も `link-output.modules[]` を `LinkedProgramModule` へ戻すだけで、helper kind を復元できない。
- validator
  - `src/toolchain/link/program_validator.py` の `LinkOutputModuleEntry` 検証は通常 module しか想定していない。
  - helper metadata を reject してはいないが、必須にもしていないため canonical lane にできない。

### 10.3 backend / writer 側の blocker

- common `ProgramWriter`
  - `src/backends/common/program_writer.py` の single-file writer は `modules` がちょうど 1 件であることを要求する。
  - helper module を canonical に流すなら、single-file backend 側で「fold 済み main artifact」と「raw helper module 群」を切り分ける契約が必要。
- C++ `ProgramWriter`
  - `src/backends/cpp/program_writer.py` は複数 module を別ファイルへ置けるが、module `kind` を見ていない。
  - 現在は `label/header_text/source_text/is_entry` だけで manifest を作るので、helper module の owner/helper_id を保持できない。
- 共通 emitter
  - `src/backends/common/emitter/code_emitter.py` は module 単位描画と dependency 収集に寄っており、optimizer-generated helper artifact を first-class input として扱わない。

### 10.4 S1-01 の結論

- 問題の主因は「C++ に別ファイルの置き場が無い」ことではない。
- 欠けているのは、`linked-program optimizer -> link-output -> backend program artifact` の全段で helper module を first-class に運ぶ canonical lane である。
- S1-02 では、`module_kind=helper`, `helper_id`, `owner_module_id`, `generated_by=linked_optimizer` を最小契約として spec に固定する。

## 決定ログ

- 2026-03-09: helper を `py_runtime.h` へ事前配置し続ける設計負債の主因は「C++ に別ファイルの置き場が無いこと」ではなく、「optimizer-generated helper artifact を中間表現として持てないこと」だと整理した。
- 2026-03-09: canonical solution は synthetic helper module を linked-program 出力へ追加し、multi-file backend は別ファイル、single-file backend は fold で扱う方式だと決定した。
- 2026-03-09: S1-01 棚卸しでは、helper の escape hatch が `py_runtime.h`、checked-in/generated runtime、emitter special-op include、backend-local inline helper に分散していること、blocker は `LinkedProgramModule` / `link-output.json` / materializer / validator / writer の全段で helper kind を持てないことだと確定した。
- 2026-03-09: S1-02 では helper artifact の最小契約を `module_kind=helper`、`meta.synthetic_helper_v1`、`helper_id`、`owner_module_id`、`generated_by=linked_optimizer` に固定し、single-file backend が fold しても runtime や inline helper 再探索へ戻してはならないと明記した。
- 2026-03-09: S2-01 では `LinkedProgramModule` / `LinkOutputModuleEntry` に `module_kind/helper_id/owner_module_id/generated_by` を追加し、validator は helper entry に `source_path=\"\"` と `generated_by=linked_optimizer` を要求する一方、raw `link-input` は helper metadata を持たないまま維持する形にした。
- 2026-03-09: S2-01 では `load_linked_output_bundle()`、global non-escape、CPP value-list hint materialization、runtime template specialization が helper metadata を落とさず引き回すことを regression test で固定した。
- 2026-03-09: S2-02 では `ir2lang` の `link-output` restart test に `module_kind=helper` / `source_path=\"\"` の synthetic helper entry を追加し、C++ multi-file restart が `__pytra_helper__.*.py` の synthetic fallback path を使って helper module doc と `meta.synthetic_helper_v1` を落とさず writer へ渡すことを固定した。
- 2026-03-09: S3-01 では host/static `build_program_artifact()` が module `kind` を canonical field として保持し、common single-file writer は `kind=helper` を primary module 候補から除外する形にした。C++ program writer も manifest に helper metadata を保持する regression を追加した。
- 2026-03-09: S3-02 では `CodeEmitter` に helper artifact registry を追加し、host/static backend registry の `collect_program_modules()` が `emit_module()` 返却物の `helper_modules` を flatten する契約を導入した。`py2x` / `ir2lang` の CLI regression で、main artifact 1 件 + helper artifact 1 件が writer の `program_artifact["modules"]` に並んで渡ることを固定した。
- 2026-03-09: S4-01 では C++ proof helper として object iteration helper を選び、`CppEmitter.enable_helper_artifact_lane` 有効時に `helper_id=cpp.object_iter` の synthetic helper module を `CodeEmitter` registry へ登録する方式にした。default path の inline lambda は保持しつつ、helper lane では `#include "<owner>_cpp_object_iter_helper.h"` と `pytra_multi_helper::object_iter_or_raise/object_iter_next_or_stop` へ切り替わることを direct emitter test で固定した。
- 2026-03-09: S4-02 では `backends.cpp.emitter.multifile_writer` が `CppEmitter.finalize_helper_artifacts()` を回収し、`kind=helper/helper_id/owner_module_id` を保持した rendered module として `ProgramWriter` へ渡す形にした。`manifest.json` と `include/src` に helper file が出力される integration test、fixture parity `3/3`、sample parity `18/18` を通し、C++ multi-file route で helper artifact lane が end-to-end で成立することを確認した。
- 2026-03-09: S5-01 では representative single-file backend proof として `ir2lang` + common `SingleFileProgramWriter` を選び、`emit_module()` が返す `helper_modules` を flatten した後でも writer は helper を別ファイル化せず main artifact だけを出力することを CLI test で固定した。
- 2026-03-09: S5-02 では helper artifact lane の docs / guard / archive を同期し、C++ multi-file と single-file fold の両方が regression test でカバーされる状態で本計画を閉じた。
