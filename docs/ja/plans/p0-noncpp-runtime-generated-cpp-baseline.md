# P0: non-C++ runtime generated lane を `cpp/generated` baseline に揃える

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01`

背景:
- `src/runtime/cpp/generated/{built_in,std,utils}/` には、SoT (`src/pytra/{built_in,std,utils}/*.py`) から materialize された canonical module baseline が存在する。
- 2026-03-13 時点の non-C++ runtime layout rollout は、この baseline 全体を各 backend の `generated/` に揃えるところまでは到達していない。
- 現行 contract / manifest / build profile は、C# `json` のように `generated blocked + native handwritten canonical` を明示的に許容している。たとえば `src/runtime/cs/native/std/json.cs` は hand-written canonical lane として残り、`src/runtime/cs/generated/std/json.cs` は存在しない。
- 同様に、`cpp/generated/utils/assertions.{h,cpp}` に対応する `src/runtime/<lang>/generated/utils/assertions.*` は多くの backend に存在しない。helper-shaped naming (`gif_helper`, `png_helper`, `image_runtime`) も残っており、module basename ベースの file compare を阻害している。
- これはユーザー指示の「まず `cpp/generated/` にある module と同じだけ各言語の `*/generated/` に生成し、それを使う」と一致しない。`generated/native` vocabulary を導入しただけでは不十分で、`generated` module set 自体を `cpp` baseline に揃える必要がある。
- したがって、本 task は「blocked / no_runtime / helper alias / native canonical 例外を温存した rollout 完了扱い」を取り消し、`cpp/generated` baseline への実体 parity を P0 として再起票する。

目的:
- C++ 以外の runtime backend (`rs`, `cs`, `go`, `java`, `kotlin`, `scala`, `swift`, `nim`, `js`, `ts`, `lua`, `ruby`, `php`) の `generated/{built_in,std,utils}` module set を、`cpp/generated/{built_in,std,utils}` の canonical baseline に揃える。
- `src/pytra/{built_in,std,utils}/*.py` から生成可能な module は、まず各 backend の `generated/` に materialize し、runtime contract でも generated lane を canonical にする。
- file compare の単位を「一部 module の compare artifact」ではなく、`cpp/generated` baseline 由来の full module set compare に引き上げる。

対象:
- `src/runtime/{rs,cs,go,java,kotlin,scala,swift,nim,js,ts,lua,ruby,php}/generated/{built_in,std,utils}/**`
- `src/runtime/<lang>/native/{built_in,std,utils}/**` の ownership 整理
- `tools/runtime_generation_manifest.json`
- `tools/gen_runtime_from_manifest.py`
- non-C++ runtime contract / checker / allowlist / inventory
- backend build profile / packaging / selfhost / smoke / runtime copy 導線
- docs / TODO / spec wording

非対象:
- `src/runtime/cpp/generated/compiler/**` と `src/runtime/cpp/generated/core/**` の non-C++ への横展開
- C++ runtime 自体の layout 再設計
- C# / non-C++ `pytra/**` checked-in tree の削除そのもの
  - これは `P0-NONCPP-RUNTIME-PYTRA-DESHIM-01` の担当とし、本 task を prerequisite とする。
- `src/pytra/**` SoT module の仕様変更
- backend ごとの生成物拡張を `cpp/generated` baseline を超えて増やすこと

## canonical generated baseline

`cpp/generated/{built_in,std,utils}` から導く canonical module baseline は次の 25 module とする。

### built_in

- `contains`
- `io_ops`
- `iter_ops`
- `numeric_ops`
- `predicates`
- `scalar_ops`
- `sequence`
- `string_ops`
- `type_id`
- `zip_ops`

### std

- `argparse`
- `glob`
- `json`
- `math`
- `os`
- `os_path`
- `pathlib`
- `random`
- `re`
- `sys`
- `time`
- `timeit`

### utils

- `assertions`
- `gif`
- `png`

注記:
- C++ の `.h/.cpp` 2-file split は compare 単位から外し、module basename 単位で比較する。
- non-C++ 側の helper-shaped basename (`gif_helper`, `png_helper`, `image_runtime`) は canonical baseline に含めない。baseline module に対しては `<module>.<ext>` naming へ寄せる。
- `compiler/` と `core/` は C++ 固有 lane のため、この task の compare baseline から外す。

受け入れ基準:
- 対象 backend すべてで、`generated/{built_in,std,utils}` の module basename 集合が canonical generated baseline と一致する。
- baseline module に対して、`blocked`, `no_runtime_module`, `helper_artifact`, `compare_artifact only`, `native canonical` を close 条件として許容しない。
- baseline module が存在する場合、backend build/runtime/selfhost/package/export はその backend の `generated/<bucket>/<module>.<ext>` を canonical module として参照する。
- `native/**` に残るのは substrate / low-level seam のみで、baseline module 自体を owner とする hand-written file (`native/std/json.cs` など) は残さない。
- contract/checker は `cpp/generated` baseline 由来の full module set compare を行い、missing module、helper alias、native-owned baseline module、baseline 外 naming drift を fail-fast にする。
- `assertions` を含む `utils` baseline が全 backend で generated lane に揃う。
- 旧 rollout の `generated ∪ blocked = baseline` ではなく、`generated = baseline` を end state として docs / checker / plan wording に固定する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_noncpp_runtime_generated_cpp_baseline_contract.py`
- `python3 tools/check_noncpp_runtime_layout_contract.py`
- `python3 tools/check_noncpp_runtime_layout_rollout_remaining_contract.py`
- `python3 tools/check_runtime_core_gen_markers.py`
- `python3 tools/check_runtime_pytra_gen_naming.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/check_multilang_selfhost_stage1.py`
- `python3 tools/check_multilang_selfhost_multistage.py`
- `find src/runtime -path '*/generated/*' -type f | sort`
- `git diff --check`

実施方針:
1. compare の正本は `cpp/generated/{built_in,std,utils}` の actual module set とする。non-C++ 側の blocked inventory から baseline を逆算してはならない。
2. baseline module で `generated` が欠けている backend は、まず generator / manifest / postprocess / emitter / substrate を修正して `generated` を出せるようにする。hand-written `native` で穴埋めしたまま close してはならない。
3. baseline module を `generated` に出せたら、build/runtime/selfhost/package を generated-first に切り替え、`native` 側の同名 owner は substrate helper へ分解するか削除する。
4. helper-shaped generated artifact (`gif_helper`, `png_helper`, `image_runtime`) は transitional naming とみなし、baseline module compare を満たす canonical naming へ寄せる。
5. `P0-NONCPP-RUNTIME-PYTRA-DESHIM-01` は本 task 完了後の follow-up とし、checked-in `pytra/**` 削除を先に進めない。

## backend family

### rs/cs

- 旧 `blocked/native canonical` 例外が最も強く残っている family。
- `json`, `assertions`, `re`, `random`, `sys`, `timeit`, `argparse` などの欠落を baseline へ揃える。

### static family

- `go`
- `java`
- `kotlin`
- `scala`
- `swift`
- `nim`

狙い:
- helper-shaped utils naming と partial built_in/std baseline を full baseline に引き上げる。

### script family

- `js`
- `ts`
- `lua`
- `ruby`
- `php`

狙い:
- generated lane の full baseline materialization と、generated-first wiring への切替を行う。
- repo-tree compat shim や package export が generated lane を隠さないようにする。

## 分解

- [ ] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01] non-C++ runtime generated lane を `cpp/generated/{built_in,std,utils}` の canonical module baseline に揃え、baseline module は各 backend の `generated/` を canonical owner にする。
- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S1-01] `cpp/generated/{built_in,std,utils}` から canonical baseline module set を実データで抽出し、plan / contract / checker の正本として固定する。
- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S1-02] 既存の `blocked / compare_artifact / no_runtime_module / helper_artifact / native canonical` 例外を baseline module には使えない契約へ切り替え、old rollout wording を active policy から外す。
- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S2-01] `rs/cs` の missing generated std/utils baseline（`json`, `assertions`, `argparse`, `random`, `re`, `sys`, `timeit` を含む）を SoT から materialize し、representative smoke / manifest / layout checker が green になるところまで揃えた。
- [ ] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S2-02] static family (`go/java/kotlin/scala/swift/nim`) の generated `built_in/std/utils` baseline を full set に引き上げ、helper-shaped naming を canonical basename に寄せる。
- [ ] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S2-03] script family (`js/ts/lua/ruby/php`) の generated `built_in/std/utils` baseline を full set に引き上げ、generated-first wiring と package/export を同期する。
- [ ] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S3-01] backend build profile / selfhost / smoke / runtime copy contract を generated-first に切り替え、baseline module の `native` owner を substrate seam へ縮退する。
- [ ] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S3-02] full file-compare contract checker を追加し、各 backend の generated module set が baseline と一致すること、helper alias や native-owned baseline module が存在しないことを fail-fast 化する。
- [ ] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S4-01] docs / TODO / inventory / archive note を同期し、`P0-NONCPP-RUNTIME-PYTRA-DESHIM-01` を後続 prerequisite 解消済みとして扱える状態にする。

決定ログ:
- 2026-03-13: ユーザー指示に従い、「`generated/native` vocabulary を導入しただけの limited compare rollout」は不十分と判断し、`cpp/generated` baseline への full generated parity を新規 P0 として起票する。
- 2026-03-13: canonical generated baseline は `cpp/generated/{built_in,std,utils}` の actual module basename 25 件とし、`compiler/core` は C++ 固有 lane として除外する。
- 2026-03-13: `P0-NONCPP-RUNTIME-PYTRA-DESHIM-01` は follow-up とし、本 task 完了前に `checked-in pytra` 削除だけを先行させない方針を明記する。
- 2026-03-13: `S1-01` として `noncpp_runtime_generated_cpp_baseline_contract.py` / checker / unit test を追加し、live `cpp/generated/{built_in,std,utils}` tree と exact-match する 25-module baseline を source of truth に固定した。
- 2026-03-13: `S1-02` として baseline module 上の legacy state (`blocked / compare_artifact / no_runtime_module / native canonical`) を compact debt inventory に固定し、helper-artifact が baseline module と交差しないことも checker で保証した。以後これらは rollout 完了条件ではなく migration debt としてのみ扱う。
- 2026-03-13: `S2-01` first bundle として `tools/runtime_generation_manifest.json` に `rs/cs` の `std/{argparse,json,random,re,sys,timeit}` と `utils/assertions` target を追加し、generated artifact を materialize した。併せて `noncpp_runtime_layout_contract.py` / smoke / unit test を更新し、`json` の `blocked` と `argparse/re` の `no_runtime_module` を compare-artifact debt まで前進させた。
- 2026-03-13: `S2-01` close bundle として `rs/cs` の representative `json/argparse/random/re/sys/timeit` smoke、manifest unit test、layout checker を green 化し、compare-artifact として残る `cs` generated lane も current SoT に refresh した。`native canonical` / `no_runtime_module` の残差は `S3-01` で generated-first wiring に寄せる。
- 2026-03-13: `S2-01` second bundle として baseline checker に `rs/cs` generated lane の missing-module guard を追加し、25-module baseline に対して `generated/{built_in,std,utils}` に欠落がないことを固定した。extra artifact（例: `rs/generated/utils/image_runtime.rs`）の exact-match 取締りは `S3-02` へ持ち越す。
