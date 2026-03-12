# P1: 残り non-C++ backend runtime を C++ 比較可能な `generated/native` layout へ段階 rollout する

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01`

背景:
- `rs/cs` は P0 で `src/runtime/<lang>/{generated,native,pytra}` へ切替済みで、P1 は残 backend (`go/java/kotlin/scala/swift/nim/js/ts/lua/ruby/php`) を同じ ownership model へ揃えるために開始した。
- この差により、`built_in/std/utils` のどの module が SoT から生成済みで、どの module が hand-written residual として残っているかを tree diff だけで比較しづらい。
- ユーザー方針として、`generated/` には SoT (`src/pytra/**`) から生成した file だけを置き、hand-written 実装を rename して押し込む運用は認めない。
- まず `rs/cs` を P0 で収束させ、残 backend は P1 で wave 単位に進める。

目的:
- 残 backend すべてについて、runtime tree の ownership を `generated/native` に揃える。
- `generated/{built_in,std,utils}` に SoT 由来 module を並べ、`native/**` には handwritten substrate / residual だけを残す。
- backend 間の compare 単位を `<lane>/<bucket>/<module>` に固定し、C++ と `rs/cs` を基準に欠落 module と residual module を比較できるようにする。

対象:
- `src/runtime/{go,java,kotlin,scala,swift,nim,js,ts,lua,ruby,php}/**`
- `tools/gen_runtime_from_manifest.py`
- `tools/runtime_generation_manifest.json`
- `src/toolchain/compiler/backend_registry_metadata.py`
- 各 backend の CLI/runtime shim/selfhost/build path 定義
- runtime guard / allowlist / inventory / docs

非対象:
- `rs/cs` runtime 自体の追加再設計
- C++ runtime 自体の再設計
- backend parity matrix の cell 実装そのもの
- 非 SoT hand-written runtime の即時全廃

受け入れ基準:
- 対象 backend すべてに `src/runtime/<lang>/{generated,native,pytra}` が存在する。
- `src/runtime/<lang>/generated/**` に存在する file は `source:` と `generated-by:` を持つ SoT 生成物だけである。
- `src/runtime/<lang>/native/**` には `generated-by:` marker が存在せず、hand-written runtime だけが残る。
- `src/runtime/<lang>/generated/{built_in,std,utils}` に、生成可能な `src/pytra/{built_in,std,utils}` module が `<lane>/<bucket>/<module>` 単位で揃う。
- 生成不能な module は backend 別 inventory/allowlist に理由付きで記録され、欠落か residual かが compare 可能である。
- backend hook / build / shim / selfhost check は新 `generated/native` path を参照する。
- runtime guard / inventory / docs は `pytra-core/pytra-gen` ではなく `generated/native` vocabulary を正本として監査する。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_noncpp_runtime_layout_rollout_remaining_contract.py`
- `python3 tools/check_runtime_core_gen_markers.py`
- `python3 tools/check_runtime_pytra_gen_naming.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/check_crossruntime_pyruntime_residual_caller_inventory.py`
- `python3 tools/check_crossruntime_pyruntime_final_thincompat_inventory.py`
- `python3 tools/check_cpp_pyruntime_contract_inventory.py`
- `python3 tools/check_multilang_selfhost_stage1.py`
- `python3 tools/check_multilang_selfhost_multistage.py`

実施方針:
1. `generated/` には rename した hand-written file を置かず、manifest/generator を通した SoT 再生成だけを許可する。
2. `native/` は current `pytra-core` の rename 先とし、substrate と residual hand-written runtime だけを残す。
3. `pytra/` は public shim / compatibility lane として当面維持してよいが、ownership 判定の正本には使わない。
4. compare 単位は `<lane>/<bucket>/<module>` に固定し、拡張子差 (`.go/.java/.kt/.scala/.swift/.nim/.js/.ts/.lua/.rb/.php`) は枝葉として扱う。
5. `generated/built_in/*` は `src/pytra/built_in/*.py` の SoT lane、`native/built_in/py_runtime.*` のような substrate は handwritten lane として分離する。

## rollout wave

### Wave A: static runtime family

対象:
- `go`
- `java`
- `kotlin`
- `scala`
- `swift`
- `nim`

狙い:
- compile-time/runtime packaging が比較的静的な backend を先に揃え、`generated/{built_in,std,utils}` と `native/**` の ownership contract を安定化する。
- `backend_registry_metadata.py` と selfhost/build check の path update を先に一般化する。

### Wave B: script runtime family

対象:
- `js`
- `ts`
- `lua`
- `ruby`
- `php`

狙い:
- runtime shim / loader / package export の差分をまとめて処理する。
- `pytra/**` compatibility lane と `generated/native` lane の責務境界を script backend 群で統一する。

## backend family ごとの作業観点

### static runtime family

- `pytra-core -> native`, `pytra-gen -> generated` rename
- manifest 出力先と runtime hook 更新
- `generated/built_in/*` の実体化
- `generated/std/*` / `generated/utils/*` の compare lane 実体化
- `native/**` に残る residual の inventory 化と縮退

### script runtime family

- `pytra-core -> native`, `pytra-gen -> generated` rename
- runtime shim / import path / require path / package export 更新
- `generated/built_in/*` の実体化
- `generated/std/*` / `generated/utils/*` の compare lane 実体化
- `pytra/**` shim と `native/**` residue の責務分離

## 分解

- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S1-01] 残 backend の current tree (`pytra-core/pytra-gen/pytra`) と target tree (`generated/native/pytra`) の対応表を backend ごとに作る。
- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S1-02] backend ごとに `generated/{built_in,std,utils}` へ載せる module、`native/**` に残す substrate/residual、blocked module を inventory/allowlist に固定する。
- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S2-01] Wave A (`go/java/kotlin/scala/swift/nim`) の path / hook / build / selfhost 定義を `generated/native` へ切り替える。
- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S2-02] Wave A の `generated/{built_in,std,utils}` を SoT から再生成し、compare lane を実体化する。
- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S2-03] Wave A の `native/**` residual を module 単位で縮退し、必要な allowlist/inventory を同期する。
- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S3-01] Wave B (`js/ts/lua/ruby/php`) の path / shim / package export / selfhost 定義を `generated/native` へ切り替える。
- [ ] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S3-02] Wave B の `generated/{built_in,std,utils}` を SoT から再生成し、compare lane を実体化する。
- [ ] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S3-03] Wave B の `native/**` residual と `pytra/**` compatibility lane の責務を整理し、必要な allowlist/inventory を同期する。
- [ ] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S4-01] cross-backend guard / inventory / docs を `generated/native` vocabulary に全面更新し、compare 不能 backend をなくす。

決定ログ:
- 2026-03-12: ユーザー指示に従い、`rs/cs` は P0、残 backend (`go/java/kotlin/scala/swift/nim/js/ts/lua/ruby/php`) は P1 に切り分けた。P1 でも `generated=SoT only`, `native=hand-written only` を維持する。
- 2026-03-12: P1 の rollout は backend 依存の packaging 差を減らすため、まず static runtime family (`go/java/kotlin/scala/swift/nim`)、次に script runtime family (`js/ts/lua/ruby/php`) の順に進める。
- 2026-03-13: `S1-01` として remaining backend ごとの current->target mapping table を `noncpp_runtime_layout_rollout_remaining_contract.py` に固定した。checker は backend 順、runtime hook key、current root 実在、lane ごとの current prefix 実在、`native/generated/compat -> native/generated/pytra` taxonomy を first bundle として監査する。
- 2026-03-13: `S1-02` の first bundle として、remaining backend ごとの current materialized file inventory (`pytra-core/pytra-gen/pytra`) を contract に固定した。blocked module や target generated/native bucket の詳細分類は後続 bundle で追加する。
- 2026-03-13: `S1-02` の later bundle として、target module bucket inventory の blocked baseline を `std/*` だけでなく canonical compare baseline（`built_in` 10 module + `std/{json,math,pathlib,time}` + `utils/{gif,png}`）へ拡張した。`kotlin/scala/swift/nim/lua/ruby` は helper-shaped image runtime のため `utils/gif|png` も blocked module として固定し、`js/ts/php` は handwritten std/native lane に残る compare module を blocked へ昇格した。
- 2026-03-13: `S1-02` の second bundle として、current inventory と lane mapping から導かれる target inventory (`generated/native/pytra`) baseline も contract に固定した。checker は ownership ごとの expected target path 集合まで監査する。
- 2026-03-13: `S1-02` の third bundle として、target inventory から導かれる logical module bucket (`generated/native/compat`) と backend ごとの blocked module baseline も contract に固定した。compat は native/generated と重複可で、blocked は canonical compare baseline の未実体化分として扱う。
- 2026-03-13: `S1-02` の final bundle として、canonical compare baseline coverage rule を contract に追加した。`blocked ⊆ compare baseline` を要求し、`generated ∩ compare baseline` と `blocked` の和集合が baseline 全体を被覆する (`generated ∪ blocked = baseline`) ことを checker で監査する。compat/native との overlap は residual shim lane を表すため許容する。
- 2026-03-13: `S2-01` として Wave A (`go/java/kotlin/scala/swift/nim`) の runtime tree を `generated/native/pytra` へ実移行し、`backend_registry_metadata.py`、manifest 出力先、runtime boundary/naming/std guard、Wave A runtime hook source contract、Java/Kotlin/Swift smoke の path baseline を同期した。`check_noncpp_runtime_layout_rollout_remaining_contract.py`、`check_runtime_{core_gen_markers,pytra_gen_naming,std_sot_guard}.py`、`check_java_pyruntime_boundary.py`、tooling unit、Kotlin/Swift smoke は通過した。
- 2026-03-13: `S2-01` の残差として、`gen_runtime_from_manifest.py --targets go,java,kotlin,scala,swift,nim` は `nim` の helper-shaped output (`png_helper.nim`) を temp output として解決できず停止し、`java/generated/std/json.java` は `--check` で再度 stale 判定になる。これらは path/hook 切替後の live regeneration 課題として `S2-02` へ持ち越す。
- 2026-03-13: `S1-02` の final bundle では、Wave A backend の一部で `generated/native/pytra` が先行実体化している mixed current state も許容するよう checker を調整した。legacy `pytra-core/pytra-gen/pytra` inventory が一致しない場合でも、そこから導出される target inventory と actual `generated/native/pytra` tree が一致すれば contract 準拠とみなす。
- 2026-03-13: `S2-02` の first bundle として、`tools/gen_runtime_from_manifest.py` は runtime 生成時に fail-soft registry ではなく `backend_registry_static` を使うように切り替え、inline text も output file も返さない backend に対して explicit error を返すようにした。これにより Nim `utils/*_helper` の停止理由が temp output path ではなく `nim native emitter: unsupported stmt kind: Try` だと確定した。
- 2026-03-13: `S2-02` の second bundle として、Java emitter の string literal escape を `\\r/\\t/\\b/\\f` まで拡張し、`src/runtime/java/generated/std/json.java` の stale compare lane を解消した。`test_gen_runtime_from_manifest.py` は explicit failure 契約と Nim `Try` blocker surfacing を監査し、`test_py2java_smoke.py` は control-character literal の regression を監査する。確認として `gen_runtime_from_manifest.py --check --targets go,java,kotlin,scala,swift` は通過し、`--targets nim --items utils/png` は `unsupported stmt kind: Try` を返す。
- 2026-03-13: `S2-02` の third bundle として、Nim native emitter に representative `Try/finally` lowering を追加し、`utils/gif_helper.nim` / `utils/png_helper.nim` を live regeneration lane へ戻した。`test_gen_runtime_from_manifest.py` は `f.write(...)` と `f.close()` の出力を監査し、`gen_runtime_from_manifest.py --targets go,java,kotlin,scala,swift,nim --check` は全通しになった。
- 2026-03-13: `S2-03` の first bundle として、Wave A `native/**` residual を contract に追加し、`built_in/py_runtime` を `substrate`、Java の `native/std/{math_impl,time_impl}` は compare label 上では `std/{math,time}` に対応する `compare_residual` として固定した。checker は module bucket と突き合わせて category overlap / bucket escape を監査する。
- 2026-03-13: `S2-03` の second bundle として、Wave A `native/**` residual の actual file inventory も contract に追加し、`go/java/kotlin/scala/swift/nim` を `built_in/py_runtime.*` only に固定した。checker は `src/runtime/<backend>/native/**` 実 tree と `substrate_files ∪ compare_residual_files` の完全一致を監査し、Java `native/std/{math_impl,time_impl}.java` は generated 側へ吸収して削除した。
- 2026-03-13: `S2-03` の follow-up bundle として、Java `generated/std/time.java` は `System.nanoTime()`、`generated/std/math.java` は `java.lang.Math` へ live-wrapper rewrite する postprocess を manifest に追加し、runtime hook metadata から `native/std/{time_impl,math_impl}.java` を外した。`test_gen_runtime_from_manifest.py` と `test_py2java_smoke.py` はこの generated-only end state を固定する。
- 2026-03-13: `S2-03` の close-out として、Wave A backend の `native/**` residual は全 backend で `built_in/py_runtime.*` substrate のみになった。compare-residual は消滅し、contract/checker/docs をこの終状態へ同期できたため `S2-03` を完了扱いにした。
- 2026-03-13: `S3-01` の first bundle として、Wave B のうち `js/ts` runtime tree を `generated/native/pytra` へ実移行した。`pytra-core -> native`、`pytra-gen -> generated`、flat compat file -> `pytra/std|utils` への正規化を行い、`js_runtime_shims.py`、selfhost JS shim writer、contract/checker、runtime dispatch test を新 path に同期した。`src/runtime/{js,ts}/pytra/**` は compat shim のみを置く。
- 2026-03-13: `S3-01` の second bundle として、`lua/ruby/php` runtime tree も `generated/native/pytra` へ実移行した。`backend_registry_metadata.py`、manifest 出力先、contract/current inventory、`check_py2x_profiles.json`、`lua/rb/php` smoke path baseline を新 path に同期し、PHP は public output bucket も `pytra/runtime/*` から `pytra/utils/*` へ正規化した。これで Wave B 全 backend の path / shim / package export baseline が `generated/native` vocabulary に揃ったため `S3-01` を完了扱いにする。
- 2026-03-13: `S3-02` の first bundle として、Wave B の既存 generated lane を live regeneration baseline として再確認した。`gen_runtime_from_manifest.py --check --targets lua,ruby,php --items utils/png,utils/gif` は全通しとなり、`audit_image_runtime_sot.py --fail-on-core-mix --fail-on-gen-markers --fail-on-non-compliant` も 14 言語すべて green になった。これで `lua/ruby/php` の generated utils lane と `lua/ruby` の `image_runtime` canonical artifact は SoT 生成物として再現可能だと確認できた。
