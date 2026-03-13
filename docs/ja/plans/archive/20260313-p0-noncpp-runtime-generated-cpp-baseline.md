# P0: non-C++ runtime generated lane を `cpp/generated` baseline に揃える

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01`

背景:
- `src/runtime/cpp/generated/{built_in,std,utils}/` には、SoT (`src/pytra/{built_in,std,utils}/*.py`) から materialize された canonical module baseline が存在する。
- 2026-03-13 時点の non-C++ runtime layout rollout は、この baseline 全体を各 backend の `generated/` に揃えるところまでは到達していない。
- 現行 contract / manifest / build profile には、Rust `pathlib/json/random/re/argparse/sys/timeit` のように `generated compare_artifact + no_runtime_module` を許容する移行負債がまだ残る。一方で baseline std owner の native canonical 残差は `generated/std` へ寄せ切ることをこの task の近傍目標とする。
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

- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01] non-C++ runtime generated lane を `cpp/generated/{built_in,std,utils}` の canonical module baseline に揃え、baseline module は各 backend の `generated/` を canonical owner にする。
- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S1-01] `cpp/generated/{built_in,std,utils}` から canonical baseline module set を実データで抽出し、plan / contract / checker の正本として固定する。
- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S1-02] 既存の `blocked / compare_artifact / no_runtime_module / helper_artifact / native canonical` 例外を baseline module には使えない契約へ切り替え、old rollout wording を active policy から外す。
- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S2-01] `rs/cs` の missing generated std/utils baseline（`json`, `assertions`, `argparse`, `random`, `re`, `sys`, `timeit` を含む）を SoT から materialize し、representative smoke / manifest / layout checker が green になるところまで揃えた。
- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S2-02] static family (`go/java/kotlin/scala/swift/nim`) の generated `built_in/std/utils` baseline を full set に引き上げ、helper-shaped naming を canonical basename に寄せる。
- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S2-03] script family (`js/ts/lua/ruby/php`) の generated `built_in/std/utils` baseline を full set に引き上げ、generated-first wiring と package/export を同期する。
- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S3-01] backend build profile / selfhost / smoke / runtime copy contract を generated-first に切り替え、baseline module の `native` owner を substrate seam へ縮退する。
- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S3-02] full file-compare contract checker を追加し、各 backend の generated module set が baseline と一致すること、helper alias や native-owned baseline module が存在しないことを fail-fast 化した。
- [x] [ID: P0-NONCPP-RUNTIME-GENERATED-CPP-BASELINE-01-S4-01] docs / TODO / inventory / archive note を同期し、`P0-NONCPP-RUNTIME-PYTRA-DESHIM-01` を後続 prerequisite 解消済みとして扱える状態にする。

決定ログ:
- 2026-03-13: ユーザー指示に従い、「`generated/native` vocabulary を導入しただけの limited compare rollout」は不十分と判断し、`cpp/generated` baseline への full generated parity を新規 P0 として起票する。
- 2026-03-13: canonical generated baseline は `cpp/generated/{built_in,std,utils}` の actual module basename 25 件とし、`compiler/core` は C++ 固有 lane として除外する。
- 2026-03-13: `P0-NONCPP-RUNTIME-PYTRA-DESHIM-01` は follow-up とし、本 task 完了前に `checked-in pytra` 削除だけを先行させない方針を明記する。
- 2026-03-13: `S1-01` として `noncpp_runtime_generated_cpp_baseline_contract.py` / checker / unit test を追加し、live `cpp/generated/{built_in,std,utils}` tree と exact-match する 25-module baseline を source of truth に固定した。
- 2026-03-13: `S1-02` として baseline module 上の legacy state (`blocked / compare_artifact / no_runtime_module / native canonical`) を compact debt inventory に固定し、helper-artifact が baseline module と交差しないことも checker で保証した。以後これらは rollout 完了条件ではなく migration debt としてのみ扱う。
- 2026-03-13: `S2-01` first bundle として `tools/runtime_generation_manifest.json` に `rs/cs` の `std/{argparse,json,random,re,sys,timeit}` と `utils/assertions` target を追加し、generated artifact を materialize した。併せて `noncpp_runtime_layout_contract.py` / smoke / unit test を更新し、`json` の `blocked` と `argparse/re` の `no_runtime_module` を compare-artifact debt まで前進させた。
- 2026-03-13: `S3-01` third bundle として C# `json` を generated-first へ切り替え、build profile / generated baseline inventory / layout contract を `src/runtime/cs/generated/std/json.cs` canonical 前提に揃えた。併せて SoT allowlist から `src/runtime/cs/native/std/json.cs` を外し、selfhost stage1/multistage checker も generated-first runtime inventory へ同期した。残る C# native canonical debt は `pathlib` だけになった。
- 2026-03-13: `S3-01` fourth bundle として C# `std/pathlib` に `cs_std_pathlib_live_wrapper` を導入し、`generated/std/pathlib.cs` を `Pytra.CsModule.py_path` facade へ再生成した。build profile / selfhost stage1/multistage / generated baseline contract / legacy layout contract / representative smoke を generated-first inventory へ同期し、`src/runtime/cs/native/std/pathlib.cs` を削除した。これで C# baseline std module に native canonical owner は残らない。
- 2026-03-13: `S2-01` close bundle として `rs/cs` の representative `json/argparse/random/re/sys/timeit` smoke、manifest unit test、layout checker を green 化し、compare-artifact として残る `cs` generated lane も current SoT に refresh した。`native canonical` / `no_runtime_module` の残差は `S3-01` で generated-first wiring に寄せる。
- 2026-03-13: `S2-01` second bundle として baseline checker に `rs/cs` generated lane の missing-module guard を追加し、25-module baseline に対して `generated/{built_in,std,utils}` に欠落がないことを固定した。extra artifact（例: `rs/generated/utils/image_runtime.rs`）の exact-match 取締りは `S3-02` へ持ち越す。
- 2026-03-13: `S2-02` first bundle として Java の missing 13 modules（`built_in/{predicates,sequence,string_ops,type_id}`, `std/{argparse,glob,os,os_path,random,re,sys,timeit}`, `utils/assertions`）を SoT から `generated/` に materialize し、`tools/runtime_generation_manifest.json`、runtime hook descriptor、legacy rollout contract、Java runtime smoke、generated-cpp baseline checker を同期した。static family の次束は `go` を先頭に full baseline 残差を潰す。
- 2026-03-13: `S2-02` current bundle として Kotlin / Scala / Swift / Nim の `generated/utils/{gif,png}` rename を contract / test / smoke expectation に反映し、`current_inventory` / `target_inventory` / `module_buckets` / `wave_a_generated_compare` / `wave_a_generated_smoke` を canonical basename 前提に同期した。`utils/image_runtime` だけを helper artifact として残し、次は static family の full-baseline 残差を `go` から埋める。
- 2026-03-13: `S2-02` third bundle として Go の missing 17 modules（`built_in/{predicates,sequence,string_ops,type_id}`, `std/{argparse,glob,json,math,os,os_path,pathlib,random,re,sys,time,timeit}`, `utils/assertions`）を SoT から `generated/` に materialize し、baseline debt contract で Go を materialized backend に昇格させた。runtime hook copy はまだ既存 substrate / image helper のまま据え置き、legacy rollout contract / representative smoke / tooling unit を full generated inventory に同期した。残る static family の full-baseline debt は Kotlin / Scala / Swift / Nim に集中する。
- 2026-03-13: `S2-02` fourth bundle として Swift の missing 17 modules（`built_in/{numeric_ops,scalar_ops,string_ops,type_id}`, `std/{argparse,glob,json,math,os,os_path,pathlib,random,re,sys,time,timeit}`, `utils/assertions`）を SoT から `generated/` に materialize し、baseline debt contract で Swift を materialized backend に昇格させた。`generated/std` lane mapping、current/target inventory、module buckets、wave-A generated compare/smoke、Swift runtime path smoke を full generated inventory に同期し、runtime hook copy は `py_runtime.swift` と `utils/image_runtime.swift` の substrate subset のまま据え置いた。残る static family の full-baseline debt は Kotlin / Scala / Nim に集中する。
- 2026-03-13: `S2-02` fifth bundle として Nim の missing 18 modules（`built_in/{io_ops,scalar_ops,sequence,string_ops,type_id}`, `std/{argparse,glob,json,math,os,os_path,pathlib,random,re,sys,time,timeit}`, `utils/assertions`）を SoT から `generated/` に materialize し、baseline debt contract で Nim を materialized backend に昇格させた。`generated/std` lane mapping、current/target inventory、module buckets、wave-A generated compare/smoke、Nim runtime path smoke を full generated inventory に同期し、runtime hook copy は `py_runtime.nim` と `utils/image_runtime.nim` の substrate subset のまま据え置いた。併せて `tools/gen_runtime_from_manifest.py` の current-file 読み出しを `newline=""` に切り替え、Nim `string_ops.nim` に含まれる raw carriage-return literal が `--check` で偽 stale 判定されないようにした。残る static family の full-baseline debt は Kotlin / Scala に集中する。
- 2026-03-13: `S2-02` sixth bundle として Kotlin の missing 18 modules（`built_in/{io_ops,numeric_ops,scalar_ops,string_ops,type_id}`, `std/{argparse,glob,json,math,os,os_path,pathlib,random,re,sys,time,timeit}`, `utils/assertions`）を SoT から `generated/` に materialize し、baseline debt contract で Kotlin を materialized backend に昇格させた。`generated/std` lane mapping、current/target inventory、module buckets、wave-A generated compare/smoke、Kotlin runtime path smoke を full generated inventory に同期し、runtime hook copy は `py_runtime.kt` と `utils/image_runtime.kt` の substrate subset のまま据え置いた。残る static family の full-baseline debt は Scala のみになった。
- 2026-03-13: `S2-02` seventh bundle として Scala の missing 18 modules（`built_in/{io_ops,numeric_ops,scalar_ops,string_ops,type_id}`, `std/{argparse,glob,json,math,os,os_path,pathlib,random,re,sys,time,timeit}`, `utils/assertions`）を SoT から `generated/` に materialize し、baseline debt contract で Scala を materialized backend に昇格させた。`generated/std` lane mapping、current/target inventory、module buckets、wave-A generated compare/smoke、Scala runtime path smoke を full generated inventory に同期した。これで static family（`go/java/kotlin/scala/swift/nim`）の full-baseline debt は解消し、`S2-02` を完了扱いにできる状態になった。
- 2026-03-13: `S2-03` first bundle として PHP の missing 9 modules（`std/{argparse,glob,os,os_path,random,re,sys,timeit}` と `utils/assertions`）を SoT から `generated/` に materialize し、`current_inventory` / `target_inventory` / `module_buckets` / manifest unit / php smoke を full generated inventory に同期した。generated-cpp baseline checker では PHP を materialized backend に昇格させたが、legacy rollout remaining contract の Wave-B compare baseline はまだ旧 16-module のままなので、新規 PHP modules は compare baseline 外 generated artifact として inventory に積んでいる。
- 2026-03-13: 同じ `S2-03` bundle で PHP emitter の case-insensitive keyword bug と `\\r` string literal escaping bug を修正し、generated `std/argparse.php` / `std/re.php` が parse 不能にならないようにした。一方で `std/glob.php` や `std/os_path.php` は PHP built-in 名と衝突して direct-load 不能なので、Wave-B generated compare smoke は既存の direct-load subset に留め、新規 PHP std/assertions modules は source-guard で代表確認する。次束は `js/ts` の full-baseline materialization に進む。
- 2026-03-13: `S2-03` second bundle として `js/ts` の missing 9 modules（`std/{argparse,glob,os,os_path,random,re,sys,timeit}` と `utils/assertions`）を SoT から `generated/` に materialize し、script family compare baseline を canonical 25-module set に揃えた。`current_inventory` / `target_inventory` / `module_buckets` / `wave_b_generated_compare` / manifest unit / `js/ts` smoke を full baseline 前提へ同期し、generated-cpp baseline checker では `js/ts` を materialized backend に昇格させた。同時に JS emitter の `JoinedStr` lowering を追加して generated `std/argparse.js` などに生の Python f-string が残らないようにし、`node --check` と source guard で parse-safe を固定した。残る script family の full-baseline debt は `lua/ruby` の helper-shaped gap である。
- 2026-03-13: `S2-03` third bundle として Ruby の `generated/{built_in,std,utils}` 25-module baseline を SoT から materialize し、`utils/{gif,png}` を `gif_helper/png_helper` から canonical basename へ rename した。`current_inventory` / `target_inventory` / `module_buckets` / `wave_b_generated_compare` / manifest unit / Ruby smoke を full baseline 前提へ同期し、generated-cpp baseline checker では Ruby を materialized backend に昇格させた。併せて Ruby emitter の class-name rendering を PascalCase 正規化し、generated `std/argparse.rb` / `std/json.rb` の `class _ArgSpec` / `class _JsonParser` 由来 parse error を解消した。残る script family の full-baseline debt は Lua の `ObjTypeId`, `pytra.std.sys` import, `string_ops` literal などの blocker 解消である。
- 2026-03-13: `S2-03` final bundle として Lua の `generated/{built_in,std,utils}` 25-module baseline を SoT から materialize し、`current_inventory` / `target_inventory` / `module_buckets` / `wave_b_generated_compare` を canonical basename 前提へ同期した。Lua emitter では `ObjTypeId`, `pytra.std.{glob,os,os_path,sys}` import alias, string literal `\\t/\\r` escaping, `string_ops` representative methods, `Try` body return handling, assignment type inference などの blocker を解消し、generated baseline checker 上の materialized backend に昇格させた。helper-shaped legacy artifact は `utils/image_runtime` だけを helper artifact として残し、`gif_helper/png_helper` は撤去した。
- 2026-03-13: `S3-01` first bundle として C# `std/math` に `cs_std_math_live_wrapper` を導入し、`generated/std/math.cs` を `System.Math` ベースの live owner 形へ再生成した。`pytra_cli_profiles.py`、selfhost stage1/multistage checker、legacy layout contract / checker / smoke を `generated/std/math.cs` 前提へ切り替え、`src/runtime/cs/native/built_in/math.cs` は residual native owner から除外して削除した。残る C# native canonical debt は `json/pathlib` と `time` backing seam である。
- 2026-03-13: `S3-01` second bundle として C# `time` の backing seam を `src/runtime/cs/native/built_in/time.cs` から `src/runtime/cs/native/std/time_native.cs` へ移し、`generated/std/time.cs` を参照する build profile / layout contract / generated baseline contract / docs を `std` vocabulary に揃えた。これで `math` と `time` はどちらも generated-first + `native/std` substrate seam で整列し、残る C# native canonical debt は `json/pathlib` に絞られた。
- 2026-03-13: `S3-01` fifth bundle として Rust `std/{time,math}` に live-wrapper postprocess を導入し、`generated/std/{time,math}.rs` を `py_runtime.rs` から `#[path = "..."]` で stage する canonical owner に切り替えた。runtime hook descriptor は `time.rs` / `math.rs` を output 側へコピーするように拡張し、layout contract / baseline contract / Rust smoke / selfhost stage1/multistage を generated-first inventory に同期した。これで Rust baseline std module の native canonical debt も解消し、`py_runtime.rs` は substrate scaffold としてだけ残る。
- 2026-03-13: `S3-01` sixth bundle として JS/TS/PHP の dead `native/std/*` residual を repo tree から削除し、selfhost stage1/multistage が生成する JS compat shim も `generated/std/*` を直参照するように切り替えた。legacy rollout contract の current/target inventory、module buckets、wave-B native residual inventory も `built_in/py_runtime` substrate のみに縮退させ、JS/TS/PHP representative smoke で再出現防止を固定した。これで baseline module の native owner 残差は解消し、`S3-01` を完了扱いにできる状態になった。
- 2026-03-13: `S3-02` second bundle として baseline contract に backend 別 `helper_artifact_modules` inventory を追加し、actual `generated/**` tree から baseline 外 module を抽出して exact-match させる checker を入れた。これにより `rs` と `kotlin/scala/swift/nim/lua/ruby` の `utils/image_runtime` だけが許容 extra artifact として明示化され、out-of-baseline generated drift は fail-fast になる。
- 2026-03-13: `S3-02` third bundle として exact runtime file inventory の expected source をこの contract の `local_runtime_file_inventory` のみに寄せ、checker / unit test から `remaining rollout` contract への merge 依存を外した。これで full file-compare の正本はこの plan/contract 側だけに閉じた。
- 2026-03-13: `S3-02` fourth bundle として generated baseline checker に残っていた `remaining rollout` contract 依存を除去し、`legacy_state_buckets` は live `rs/cs` layout contract だけから再構成、helper overlap は actual helper inventory から算出、`remaining_helper_inventory` は baseline contract の allowlist をそのまま正本として参照する形へ整理した。これで `S3-02` の full file-compare checker は `noncpp_runtime_generated_cpp_baseline_contract.py` と live tree だけで閉じた。
- 2026-03-13: `S4-01` として plan を `docs/ja/plans/archive/20260313-p0-noncpp-runtime-generated-cpp-baseline.md` へ移し、active TODO から親 P0 を外して archive history に記録した。close 後の最上位 follow-up は `P0-NONCPP-RUNTIME-PYTRA-DESHIM-01` だけである。
