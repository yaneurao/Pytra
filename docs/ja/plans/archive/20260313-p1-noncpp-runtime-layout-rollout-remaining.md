<a href="../../../en/plans/archive/20260313-p1-noncpp-runtime-layout-rollout-remaining.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

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
- `tools/gen/gen_runtime_from_manifest.py`
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
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_noncpp_runtime_layout_rollout_remaining_contract.py`
- `python3 tools/check/check_runtime_core_gen_markers.py`
- `python3 tools/check/check_runtime_pytra_gen_naming.py`
- `python3 tools/check/check_runtime_std_sot_guard.py`
- `python3 tools/check/check_crossruntime_pyruntime_residual_caller_inventory.py`
- `python3 tools/check/check_crossruntime_pyruntime_final_thincompat_inventory.py`
- `python3 tools/check/check_cpp_pyruntime_contract_inventory.py`
- `python3 tools/check/check_multilang_selfhost_stage1.py`
- `python3 tools/check/check_multilang_selfhost_multistage.py`

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
- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S3-02] Wave B の `generated/{built_in,std,utils}` を SoT から再生成し、compare lane を実体化する。
- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S3-03] Wave B の `native/**` residual と `pytra/**` compatibility lane の責務を整理し、必要な allowlist/inventory を同期する。
- [x] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01-S4-01] cross-backend guard / inventory / docs を `generated/native` vocabulary に全面更新し、compare 不能 backend をなくす。

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
- 2026-03-13: `S2-02` の first bundle として、`tools/gen/gen_runtime_from_manifest.py` は runtime 生成時に fail-soft registry ではなく `backend_registry_static` を使うように切り替え、inline text も output file も返さない backend に対して explicit error を返すようにした。これにより Nim `utils/*_helper` の停止理由が temp output path ではなく `nim native emitter: unsupported stmt kind: Try` だと確定した。
- 2026-03-13: `S2-02` の second bundle として、Java emitter の string literal escape を `\\r/\\t/\\b/\\f` まで拡張し、`src/runtime/java/generated/std/json.java` の stale compare lane を解消した。`test_gen_runtime_from_manifest.py` は explicit failure 契約と Nim `Try` blocker surfacing を監査し、`test_py2java_smoke.py` は control-character literal の regression を監査する。確認として `gen_runtime_from_manifest.py --check --targets go,java,kotlin,scala,swift` は通過し、`--targets nim --items utils/png` は `unsupported stmt kind: Try` を返す。
- 2026-03-13: `S2-02` の third bundle として、Nim native emitter に representative `Try/finally` lowering を追加し、`utils/gif_helper.nim` / `utils/png_helper.nim` を live regeneration lane へ戻した。`test_gen_runtime_from_manifest.py` は `f.write(...)` と `f.close()` の出力を監査し、`gen_runtime_from_manifest.py --targets go,java,kotlin,scala,swift,nim --check` は全通しになった。
- 2026-03-13: `S2-03` の first bundle として、Wave A `native/**` residual を contract に追加し、`built_in/py_runtime` を `substrate`、Java の `native/std/{math_impl,time_impl}` は compare label 上では `std/{math,time}` に対応する `compare_residual` として固定した。checker は module bucket と突き合わせて category overlap / bucket escape を監査する。
- 2026-03-13: `S2-03` の second bundle として、Wave A `native/**` residual の actual file inventory も contract に追加し、`go/java/kotlin/scala/swift/nim` を `built_in/py_runtime.*` only に固定した。checker は `src/runtime/<backend>/native/**` 実 tree と `substrate_files ∪ compare_residual_files` の完全一致を監査し、Java `native/std/{math_impl,time_impl}.java` は generated 側へ吸収して削除した。
- 2026-03-13: `S2-03` の follow-up bundle として、Java `generated/std/time.java` は `System.nanoTime()`、`generated/std/math.java` は `java.lang.Math` へ live-wrapper rewrite する postprocess を manifest に追加し、runtime hook metadata から `native/std/{time_impl,math_impl}.java` を外した。`test_gen_runtime_from_manifest.py` と `test_py2java_smoke.py` はこの generated-only end state を固定する。
- 2026-03-13: `S2-03` の close-out として、Wave A backend の `native/**` residual は全 backend で `built_in/py_runtime.*` substrate のみになった。compare-residual は消滅し、contract/checker/docs をこの終状態へ同期できたため `S2-03` を完了扱いにした。
- 2026-03-13: `S3-01` の first bundle として、Wave B のうち `js/ts` runtime tree を `generated/native/pytra` へ実移行した。`pytra-core -> native`、`pytra-gen -> generated`、flat compat file -> `pytra/std|utils` への正規化を行い、`js_runtime_shims.py`、selfhost JS shim writer、contract/checker、runtime dispatch test を新 path に同期した。`src/runtime/{js,ts}/pytra/**` は compat shim のみを置く。
- 2026-03-13: `S3-01` の second bundle として、`lua/ruby/php` runtime tree も `generated/native/pytra` へ実移行した。`backend_registry_metadata.py`、manifest 出力先、contract/current inventory、`check_py2x_profiles.json`、`lua/rb/php` smoke path baseline を新 path に同期し、PHP は public output bucket も `pytra/runtime/*` から `pytra/utils/*` へ正規化した。これで Wave B 全 backend の path / shim / package export baseline が `generated/native` vocabulary に揃ったため `S3-01` を完了扱いにする。
- 2026-03-13: `S3-02` の first bundle として、Wave B の既存 generated lane を live regeneration baseline として再確認した。`gen_runtime_from_manifest.py --check --targets lua,ruby,php --items utils/png,utils/gif` は全通しとなり、`audit_image_runtime_sot.py --fail-on-core-mix --fail-on-gen-markers --fail-on-non-compliant` も 14 言語すべて green になった。これで `lua/ruby/php` の generated utils lane と `lua/ruby` の `image_runtime` canonical artifact は SoT 生成物として再現可能だと確認できた。
- 2026-03-13: `S3-02` の next bundle として、Lua runtime regeneration が `pytra.utils.gif` 内の `from pytra.std import abi` で停止していたため、Lua emitter の import alias 解決で compile-time decorator import（`abi/template/extern`）を無視する seam を追加した。`test_gen_runtime_from_manifest.py` に regression を足し、`gen_runtime_from_manifest.py --targets js,ts,lua,ruby,php --check` が再び全通しになることを確認した。
- 2026-03-13: `S3-02` の current bundle として、Wave B 全体の `gen_runtime_from_manifest.py --targets js,ts,lua,ruby,php --check` green 状態を `test_gen_runtime_from_manifest.py` の unit test に固定した。これで `lua/ruby/php` の utils compare lane だけでなく、`js/ts` を含む Wave B script runtime family 全体の compare lane が tooling regression として監視される。
- 2026-03-13: `S3-02` の current bundle として、Wave B blocked compare lane を `missing compare lane / native residual / helper-shaped gap` の 3 類型へ分類した。`js/ts` は `std/{math,pathlib,time}` を handwritten native residual、`std/json` と `built_in/*` を missing compare lane、`php` は `std/time` を native residual とし、`lua/ruby` は canonical baseline 全体を helper-shaped gap として contract/checker で固定した。
- 2026-03-13: `S3-02` の current bundle として、`js/ts/php` の `std/time` を SoT から live-generated compare lane に昇格した。`tools/gen/gen_runtime_from_manifest.py` に `js/ts/php` 向け `std/time` live-wrapper postprocess を追加し、`src/runtime/{js,ts,php}/generated/std/time.*` を再生成、`src/runtime/{js,ts,php}/pytra/std/time.*` と `js_runtime_shims.py`、PHP runtime packaging を generated 側へ切り替えた。contract/checker と tooling/smoke を同期し、Wave B blocked compare baseline から `std/time` を外した。
- 2026-03-13: `S3-02` の current bundle として、`js/ts` の `std/math` を SoT から live-generated compare lane に昇格した。`tools/gen/gen_runtime_from_manifest.py` に `js/ts` 向け `std/math` live-wrapper postprocess を追加し、`src/runtime/{js,ts}/generated/std/math.*` を再生成、`src/runtime/{js,ts}/pytra/std/math.*` と `js_runtime_shims.py` を generated 側へ切り替えた。contract/checker と tooling/smoke を同期し、`js/ts` の blocked compare baseline から `std/math` を外した。
- 2026-03-13: `S3-02` の current bundle として、`php` の `std/math` を SoT から live-generated compare lane に昇格した。`tools/gen/gen_runtime_from_manifest.py` に `php` 向け `std/math` live-wrapper postprocess を追加し、`src/runtime/php/generated/std/math.php` を再生成、`src/runtime/php/pytra/std/math.php` を thin compat として追加し、PHP runtime packaging も `std/math.php` を配布するように更新した。contract/checker と tooling/smoke を同期し、`php` の blocked compare baseline から `std/math` を外した。
- 2026-03-13: `S3-02` の final bundle として、Wave B generated compare end state を contract/checker で固定した。`js/ts/php` は compare baseline のうち `std/{math,time}` と `utils/{gif,png}` を materialized generated lane とし、`lua/ruby` は compare baseline 側の live laneを持たず `utils/{gif_helper,image_runtime,png_helper}` の helper-shaped generated artifact のみを残す。これで Wave B の generated compare 実体化範囲と residual helper lane が明示的になったため `S3-02` を完了扱いにする。
- 2026-03-13: `S3-03` の first bundle として、Wave B native residual の responsibility baseline を contract/checker に追加した。`js/ts` は `built_in/py_runtime` と native backing seam の `std/{math,pathlib,time}` を substrate、`php` は `built_in/py_runtime` と `std/time` を substrate、`lua/ruby` は `built_in/py_runtime` のみを substrate として固定した。module/file inventory の 2 面を監査することで、次の compat allowlist bundle が native residual cleanup と競合しない状態にした。
- 2026-03-13: `S3-03` の next bundle として、`js/ts` の `std/pathlib` を SoT から live-generated compare lane に昇格した。`tools/gen/gen_runtime_from_manifest.py` と `tools/runtime_generation_manifest.json` に `js/ts` 向け `std/pathlib` live-wrapper postprocess を追加し、`src/runtime/{js,ts}/generated/std/pathlib.*` を再生成、`src/runtime/{js,ts}/pytra/std/pathlib.*` と `js_runtime_shims.py` を generated 側へ切り替えた。contract/checker と tooling/smoke を同期し、`js/ts` の blocked compare baseline を `built_in/* + std/json` のみに縮退させつつ、native `std/pathlib` は後続 cleanup まで substrate として維持する。
- 2026-03-13: `S3-03` の current bundle として、`php` の `std/pathlib` を SoT から live-generated compare lane に昇格した。`tools/gen/gen_runtime_from_manifest.py` と `tools/runtime_generation_manifest.json` に `php` 向け `std/pathlib` live-wrapper postprocess を追加し、`src/runtime/php/generated/std/pathlib.php` を再生成、`src/runtime/php/pytra/std/pathlib.php` compat と PHP runtime packaging を generated 側へ拡張した。contract/checker と tooling/smoke を同期し、`php` の blocked compare baseline も `built_in/* + std/json` まで縮退させた。
- 2026-03-13: `S3-03` の current bundle として、Wave B の `pytra/**` compatibility lane を `substrate shim` と `generated compare shim` に分けて contract/checker に追加した。`js/ts/php` は `built_in/py_runtime` を substrate shim、`std/{math,pathlib,time}` と `utils/{gif,png}` を generated compare shim とし、`lua/ruby` は `built_in/py_runtime` shim のみを持つ形に固定した。module/file inventory の 2 面を監査することで、native residual cleanup と public compat shim cleanup の境界が比較可能になった。
- 2026-03-13: 同じ `S3-03` bundle として、PHP generated wrapper が repo 上でも native `built_in/py_runtime.php` substrate shim を辿れるように require fallback を補強した。`generated/std/{math,pathlib}` と `generated/utils/{gif,png}` が `pytra/**` compat lane と native substrate を横断して動く representative smoke を固定した。
- 2026-03-13: 次の `S3-03` bundle として、PHP の compat lane から未参照の `pytra/std/{math,pathlib}.php` を削除した。`pytra/std/time.php` だけを残し、contract/checker は `generated compare lane` と `compat shim lane` が一致しなくてもよい形へ縮退させた。これで PHP の public compat 責務は root `py_runtime.php` と `std/time.php`、`utils/{gif,png}.php` に限定され、`std/{math,pathlib}` は generated compare artifact のみとして扱える。
- 2026-03-13: 同じ `S3-03` bundle として、`lua/ruby` の `pytra/built_in/py_runtime.*` compat shim を repo tree から直接 load する representative smoke を追加した。これで Wave B compat shim baseline は PHP generated wrapper の substrate fallback だけでなく、`lua/ruby` の substrate helper (`__pytra_truthy`) direct execution も回帰監視できる。
- 2026-03-13: 続く `S3-03` bundle として、`js/ts` の `std/json` を SoT から live-generated compare lane に昇格した。`tools/gen/gen_runtime_from_manifest.py` と `tools/runtime_generation_manifest.json` に `js/ts` 向け `std/json` live-wrapper postprocess を追加し、`src/runtime/{js,ts}/generated/std/json.*` を再生成、`src/runtime/{js,ts}/pytra/std/json.*` と `js_runtime_shims.py` を generated 側へ切り替えた。contract/checker と tooling/smoke を同期し、`js/ts` の Wave B blocked compare baseline を `built_in/*` のみに縮退させた。
- 2026-03-13: 続く `S3-03` bundle として、`js` の public compat shim も repo tree から直接 `require(...)` する representative smoke を追加した。`pytra/py_runtime.js` と `pytra/std/pathlib.js` を直接 load して `pyBool` と `Path(...)` を確認し、script backend compat lane の direct-load regression を `lua/ruby` substrate shim と並行して固定した。
- 2026-03-13: 続く `S3-03` bundle として、`php` の remaining public compat shim も repo tree から直接 `require` する representative smoke を追加した。`pytra/py_runtime.php` と `pytra/std/time.php` を直接 load して `__pytra_truthy` と `perf_counter()` を確認し、compat lane が `std/time` だけに縮退した後も public shim surface が直接実行可能であることを固定した。
- 2026-03-13: 同じ `S3-03` bundle として、remaining public compat shim の direct-load coverage を拡張した。`js` では `pytra/std/{math,time}.js` と `pytra/utils/{gif,png}.js`、`php` では `pytra/utils/{gif,png}.php` まで repo tree から直接 load して representative export/function を確認し、Wave B compat lane の public surface が generated compare shim 側まで回帰監視されるようにした。
- 2026-03-13: 続く `S3-03` bundle として、Wave B の public compat smoke inventory を contract/checker に追加した。`js/php/lua/ruby` は repo tree からの `direct_load`、`ts` は `.ts` source のため `source_reexport` として扱い、`pytra/**` public shim のうち representative に監視する file set を exact baseline で固定した。
- 2026-03-13: 続く `S3-03` bundle として、`php` の `std/json` を SoT から live-generated compare lane に昇格した。generator を通すために PHP emitter の `RuntimeIter` tuple target を `dict.items()` 向け key/value `foreach` まで下ろし、`tools/gen/gen_runtime_from_manifest.py` と `tools/runtime_generation_manifest.json` に `php std/json` live-wrapper postprocess を追加して `src/runtime/php/generated/std/json.php` を再生成、PHP runtime packaging も generated 側へ拡張した。contract/checker と tooling/smoke を同期し、`php` の Wave B blocked compare baseline を `built_in/*` のみに縮退させた。
- 2026-03-13: `S3-03` の close-out として、Wave B script runtime family の `native residual / compat shim / blocked compare / public compat smoke` の 4 面が contract/checker と representative smoke で揃った。`js/ts/php` は `built_in/py_runtime` substrate shim と generated compare shim、`lua/ruby` は substrate shim only、`blocked` は全 backend で `built_in/*` または helper-shaped gap だけに縮退したため、責務境界の整理は完了とみなして `S3-03` を閉じる。
- 2026-03-13: `S4-01` の first bundle として、Wave B script backend に不足していた `generated/built_in/*` compare baseline を `js/ts/php` へ拡張した。`tools/runtime_generation_manifest.json` と `tools/gen/gen_runtime_from_manifest.py` に JS/TS CJS built_in postprocess を追加し、`contains/io_ops/iter_ops/numeric_ops/predicates/scalar_ops/sequence/string_ops/type_id/zip_ops` を `js/ts/php` の generated compare target として固定した。`test_gen_runtime_from_manifest.py` では built_in manifest baseline を `rs/cs only` から `compare targets` 全体に引き上げ、`test_py2js_smoke.py` / `test_py2ts_smoke.py` / `test_py2php_smoke.py` では `generated/built_in/{contains,predicates,sequence}` の representative smoke を追加して repo tree からの direct-load / source check を固定した。
- 2026-03-13: `S4-01` の current bundle として、Wave B generated compare smoke inventory を contract/checker に追加した。`js/php` は `generated/built_in/{contains,predicates,sequence}` の repo-tree direct-load smoke、`ts` は `generated/built_in/{contains,sequence}` の source-guard smoke を baseline とし、representative built_in compare smoke の backend ごとの検証手段を `generated/native` vocabulary で固定した。
- 2026-03-13: `S4-01` の current bundle として、`go/java` の generated `built_in` compare baseline を manifest / contract に追加した。`contains/io_ops/iter_ops/numeric_ops/scalar_ops/zip_ops` を compile-safe subset として `generated/built_in/*` へ materialize し、`go` は runtime bundle compile smoke、`java` は small compile/run smoke、Wave A 全体は `source_guard` inventory で representative generated targets を固定した。これで static runtime family 側でも generated compare/helper lane の検証手段が `generated/native` vocabulary で揃った。
- 2026-03-13: `S4-01` の current bundle として、Wave A generated compare smoke inventory を contract/checker に分離した。`go/java` は `generated/built_in/contains.*` を `build_run_smoke`、`kotlin/scala/swift/nim` は helper-shaped `generated/utils/*` を `source_guard` として固定し、static runtime family の generated compare evidence taxonomy を `generated/native` vocabulary で明示した。
- 2026-03-13: `S4-01` の current bundle として、`kotlin/scala/nim` の generated `built_in` compare baseline を manifest / contract に追加した。`kotlin/scala` は `contains/iter_ops/predicates/sequence/zip_ops`、`nim` は `contains/iter_ops/numeric_ops/predicates/zip_ops` を compile-safe subset として `generated/built_in/*` へ materialize し、`tools/gen/gen_runtime_from_manifest.py` には Kotlin/Scala の空 `main` を剥がす `program_to_library` postprocess を追加した。checker と tooling/backends smoke は `kotlin/nim = build_run_smoke`, `scala = source_guard` へ同期し、Wave A の compare-impossible backend は `swift` のみに縮退した。`swift` は native substrate に `__pytra_as_list` など generated built_in 側が要求する helper が不足しているため、この slice では blocked のまま据え置く。
- 2026-03-13: `S4-01` の current bundle として、`swift` native substrate に `__pytra_as_list` / `__pytra_as_dict` を追加し、`tools/gen/gen_runtime_from_manifest.py` へ Swift の空 `@main` を剥がす `program_to_library` postprocess を追加した。これにより `contains/io_ops/iter_ops/predicates/sequence/zip_ops` を compile-safe subset として `src/runtime/swift/generated/built_in/*` へ materialize できるようになり、contract/checker と Swift build-run smoke を同期した。Wave A の compare-impossible backend set はこれで空になった。
- 2026-03-13: `S4-01` の close-out として、Wave A/Wave B の generated compare baseline、smoke taxonomy、blocked/helper-shaped gap inventory、compat/native residual boundary がすべて `generated/native` vocabulary へ揃った。remaining backend で compare-impossible set は解消済みで、`go/java/kotlin/scala/swift/nim/js/ts/lua/ruby/php` 全 backend が cross-backend guard / inventory / docs 上で file-level compare 可能になったため、P1 全体を完了として archive へ移す。
