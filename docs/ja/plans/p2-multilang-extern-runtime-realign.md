# P2: 全言語 `@extern` runtime/emitter 契約の再整列

最終更新: 2026-03-14

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01`

背景:
- `src/pytra/std/math.py`、`src/pytra/std/time.py`、`src/pytra/std/os.py`、`src/pytra/std/os_path.py`、`src/pytra/std/sys.py`、`src/pytra/std/glob.py`、`src/pytra/built_in/io_ops.py`、`src/pytra/built_in/scalar_ops.py` などは `@extern` / `extern(...)` を使って runtime 外部境界を宣言している。
- 2026-03-13 時点の非 C++ lane では、この宣言が generated runtime postprocess や backend emitter の special case によって host API 直結へ畳み込まれている。
- 代表例として `src/runtime/cs/generated/std/math.cs` は `System.Math` 実装と source に存在しない `tau` を持ち、`tools/gen_runtime_from_manifest.py` と各 backend emitter に `pytra.std.math` 固有知識が分散している。
- この状態では `src/pytra/**` が SoT にならず、`@extern` が「外部境界宣言」ではなく「backend が勝手に host API 実装へ潰してよい印」として誤用されている。
- C++ は header/source 分離で `extern` 宣言と native 実装の分離が比較的守られており、非 C++ も同じ原理へ戻す必要がある。

目的:
- `@extern` を全言語で共通の「外部境界宣言」として扱い直し、generated lane から host 固有意味論を追い出す。
- host API への接続は `src/runtime/<lang>/native/**` の ownership に集約し、backend emitter は generic extern metadata だけを見る構造へ戻す。
- `src/pytra/**` の API surface を正本に戻し、source にない symbol 追加や module-specific rewrite を止める。

対象:
- `src/pytra/std/*` / `src/pytra/built_in/*` にある runtime SoT の `@extern` / `extern(...)`
- `tools/runtime_generation_manifest.json` と `tools/gen_runtime_from_manifest.py`
- 各 backend emitter にある `pytra.std.math` など module-specific extern special case
- runtime symbol index / layout contract / representative smoke / docs の extern ownership 記述
- 全 target language の generated/native runtime artifact 更新

非対象:
- user program 側の ambient global `extern()`（`document`, `window.document` など）の意味論拡張
- `@extern` 以外の runtime helper 全般の redesign
- host runtime API の機能追加

受け入れ基準:
- generated runtime artifact が `@extern` symbol の host 固有実装を直書きしない。
- `System.Math` / `Math.*` / `pyMath*` など host binding は `src/runtime/<lang>/native/**` の canonical owner に閉じる。
- backend emitter から `pytra.std.math` のような module-specific extern hardcode が撤去され、generic extern/runtime metadata 経由へ揃う。
- `src/pytra/**` に存在しない symbol（例: `tau`）を generated artifact が勝手に追加しない。
- C++ reference lane を壊さず、非 C++ 全 target の representative runtime/emitter regression が current contract に更新される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `rg -n "std_math_live_wrapper|pytra\\.std\\.math|System\\.Math|Math\\.PI|Math\\.Sqrt|tau" src tools test docs -g '!**/archive/**'`
- `python3 tools/gen_runtime_from_manifest.py --items std/math,std/time,std/os,std/os_path,std/sys,std/glob,built_in/io_ops,built_in/scalar_ops --targets rs,cs,js,ts,go,java,swift,kotlin,ruby,lua,scala,php,nim`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_gen_runtime_from_manifest.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2*_smoke.py'`
- `git diff --check`

## 分解

- [x] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S1-01] runtime SoT 上の `@extern` module と、generated rewrite / emitter hardcode / native owner の current inventory を全 target で棚卸しする。
- [x] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S1-02] `@extern` を「宣言のみ」「native owner 実装」「ambient extern は別系統」に分けた cross-target contract を spec / plan に固定する。
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S2-01] `tools/runtime_generation_manifest.json` と `tools/gen_runtime_from_manifest.py` から module-specific extern rewrite を除去し、generated lane を declaration/wrapper-only に揃える。
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S2-02] 各 target の `src/runtime/<lang>/native/**` に extern-backed canonical owner を整備し、runtime symbol index / layout contract を同期する。
- [x] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S2-03] 各 backend emitter の `pytra.std.math` など module-specific extern hardcode を撤去し、generic extern/runtime metadata 経由へ移す。
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S3-01] representative runtime artifact / smoke / docs / contract inventory を current extern ownership contract に同期して task を閉じる。

`S1-02` として、runtime SoT `@extern` を declaration-only、native owner 実装を runtime layout / manifest / runtime symbol index、ambient global `extern()` を別系統に固定する contract/checker/spec wording を追加した。

決定ログ:
- 2026-03-13: ユーザー指摘により、`@extern` を backend shortcut として扱っていた現行非 C++ 設計を誤りと認め、全 target を対象に SoT/native-owner/generic-emitter へ戻す P2 task として起票した。
- 2026-03-14: manifest/emitter の hardcode を直接剥がす前段として、`tools/gen_runtime_symbol_index.py` と `runtime_symbol_index.py` に `extern_contract_v1` / `extern_v1` を追加し、runtime SoT 上の `@extern` module/symbol を generic metadata として引ける状態にした。
- 2026-03-14: C# は既存の `time_native` pattern に合わせ、`generated/std/math.cs` を `math_native` へ委譲する wrapper に戻し、`System.Math` 直書きを `src/runtime/cs/native/std/math_native.cs` へ押し込めた。
- 2026-03-14: `math_native` seam に合わせて C# smoke、non-C++ runtime layout contract、generated-cpp baseline contract、CLI build profile、selfhost compile checker を同期し、`generated/std/math.cs` が native seam なしでは成立しない状態を消した。
- 2026-03-14: 最初の realignment slice として、SoT に存在しない `tau` を C# `std/math` generated wrapper が勝手に追加していた挙動を止め、`pi/e` のみを source-of-truth とする状態へ戻した。
- 2026-03-14: `S1-01` として `multilang_extern_runtime_realign_inventory.py` / checker / unit test を追加し、`std/math,time,os,os_path,sys,glob` と `built_in/io_ops,scalar_ops` の manifest postprocess・C++ native owner・non-C++ native seam・emitter hardcode・generated drift を current worktree 基準で固定した。C# `std/math` は `math_native.cs` seam を current non-C++ owner として inventory に含めた。
- 2026-03-14: C# emitter では `CodeEmitter.get_import_resolution_bindings()` / `lookup_import_resolution_binding()` から得る canonical extern metadata と `iter_cs_std_lane_ownership()` を使って `std/math` / `std/time` owner 解決を generic 化し、`pytra.std.math` / `pytra.std.time` 文字列 hardcode への依存を 1 段減らした。
- 2026-03-14: `S1-02` として、runtime SoT `@extern` を declaration-only、native owner 実装を runtime layout / manifest / runtime symbol index、ambient global `extern()` を別系統に固定する contract/checker/spec wording を追加した。
- 2026-03-14: Rust emitter では `iter_rs_std_lane_ownership()` から作る runtime prelude re-export module 集合で root `use` 抑止と prelude export を組み立て、`pytra.std.time` の直文字列 hardcode を inventory から外した。
- 2026-03-14: `tools/gen_runtime_from_manifest.py` の C# `std/time` rewrite も `helper_name + "_native"` へ委譲する共通 `cs_std_native_owner_wrapper` に揃え、`time_native` 固定の one-off postprocess を manifest から外した。
- 2026-03-14: Nim emitter では `std/math` の `sqrt` / `pi` / `e` special handling を runtime module literal ではなく `semantic_tag` と `runtime_symbol` から判定する形へ寄せ、`pytra.std.math` needle を inventory から外した。
- 2026-03-14: PHP/Ruby emitter では zero-arg runtime value getter 判定を `lookup_runtime_symbol_extern_doc(...).kind == "value"` ベースへ切り替え、`pytra.std.math` 否定条件の needle を inventory から外した。
- 2026-03-14: Go/Kotlin/Swift emitter では `std/math` 判定を `pytra.std.math` literal から、runtime extern module metadata と math symbol set の組み合わせへ寄せ、`_runtime_module_id(expr) == "pytra.std.math"` needle を inventory から外した。
- 2026-03-14: `S2-01` first bundle として `tools/runtime_generation_manifest.json` の C# `std/time` postprocess 名を `cs_std_native_owner_wrapper` に generic 化し、`tools/gen_runtime_from_manifest.py` でも `rewrite_cs_std_time_live_wrapper` を generic owner-wrapper helper へ置き換えた。`time_native` seam はそのまま canonical owner として維持する。
- 2026-03-14: `S2-01` second bundle として `std/time` の `rs/java/js/ts/php` postprocess 名を generic `perf_counter` seam helper に改名し、`tools/gen_runtime_from_manifest.py` と inventory/checker から module-specific `*_std_time_live_wrapper` naming を外した。
- 2026-03-14: PHP/Ruby emitter では `std/math` の `pi` / `e` zero-arg getter 判定を `lookup_runtime_symbol_extern_doc(...).kind == "value"` と `runtime_symbol` へ寄せ、`if _runtime_module_id(expr) != "pytra.std.math"` 形式の module literal hardcode を inventory から外した。value getter adapter metadata 自体はまだ未モデルなので、現段階では symbol set は `pi` / `e` のまま維持する。
- 2026-03-14: runtime symbol index に `math.float_args` / `math.value_getter` adapter metadata を追加し、Scala emitter の `std/math` host shortcut を `pyMath*` helper 呼び出しへ戻した。self-hosted lane は adapter metadata、既存 backend-only IR compare artifact は `math.pi` / `math.sin` 形式の fallback で吸収し、`scala.math.*` / `pytra.std.math` literal を inventory から外した。
- 2026-03-14: Lua emitter では `std/math` module/symbol alias を `math.float_args` / `math.value_getter` adapter metadata で、`std/time` alias を `stdlib.fn.perf_counter` semantic tag で判定する形へ寄せた。これで `if mod == "pytra.std.math"` / `if mod == "pytra.std.time"` needle を inventory から外し、Lua import lowering の `math` / `perf_counter` smoke を generic metadata 経由へ揃えた。
- 2026-03-14: 同じ Lua slice で `std/glob`, `std/os`, `std/os_path`, `std/sys` も `semantic_tag` から symbol table alias を組み立てる形へ寄せ、`if mod == "pytra.std.glob|os|os_path|sys"` literal hardcode を inventory から外した。Lua 側の残り module-specific alias hardcode は `enum`, `argparse`, `re`, `json`, `pathlib`, `pytra.utils.*` だけになった。
- 2026-03-14: Lua emitter の `std/os`, `std/os_path`, `std/sys`, `std/glob` も semantic tag ベースの symbol-table alias へ寄せ、`if mod == "pytra.std.*"` literal hardcode を inventory から外した。Lua import lowering は `os.getcwd`, `os_path.join`, `sys.write_stdout`, `glob.glob` を generic extern metadata 経由で通すように揃えた。
- 2026-03-14: `S2-03` を docs へ反映し、emitter hardcode inventory が全 row green になった状態を plan/todo に同期した。
- 2026-03-14: `S3-01` first bundle として inventory に `representative_smoke_needles` を追加し、`std/math/time` は C#/Go/Java/Rust、`std/os/os_path/sys/glob` は Lua/JS/TS/PHP、`built_in/io_ops/scalar_ops` は Go/Kotlin/Scala/Swift の smoke evidence へ固定した。
- 2026-03-14: JS/TS `std/math` では generated wrapper から `Math.*` / `Math.PI` の host binding を除き、`src/runtime/js|ts/native/std/math_native.*` を canonical seam として追加した。あわせて baseline/rollout contract と JS/TS smoke を同期し、generated lane が native owner だけを見る形へ戻した。
- 2026-03-14: `S2-01` の追加 slice として、C# `std/math` は module-specific `cs_std_math_live_wrapper` をやめて既存の `cs_std_native_owner_wrapper` に統合し、JS `std/math` も `js_std_native_owner_wrapper + helper_name=math` へ寄せた。どちらも raw generated text から extern value/function の順序を拾って `math_native` seam へ forward する形に揃えた。
- 2026-03-14: 同じ `S2-01` の続きとして、TS `std/math` も `ts_std_native_owner_wrapper + helper_name=math` へ寄せた。raw generated text から function/value の順序を拾い、numeric signature を postprocess 側で再付与しつつ `math_native` seam へ forward する形に統一した。
- 2026-03-14: Java `std/time` は `generated/std/time.java` から `System.nanoTime()` を除き、`src/runtime/java/native/std/time_native.java` を canonical seam として追加した。runtime hook metadata、rollout/baseline contract、inventory、Java smoke をこの seam 前提へ同期した。
- 2026-03-14: JS/TS `std/time` でも同じ分離を適用し、`generated/std/time.{js,ts}` から `process.hrtime.bigint()` を除去して `src/runtime/js|ts/native/std/time_native.*` へ委譲する wrapper に戻した。inventory / rollout contract / baseline contract / JS/TS smoke も time seam 前提へ同期した。
