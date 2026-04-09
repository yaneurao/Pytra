<a href="../../en/todo/lua.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Lua backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-10（guide cleanup 着手、Lua fixture/stdlib は 2026-04-02 基準）

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/lua/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/lua/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の Lua emitter: `src/toolchain/emit/lua/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の Lua runtime: `src/runtime/lua/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-LUA-EMITTER-GUIDE-CLEANUP: Lua emitter の guide 違反を除去する

文脈: [docs/ja/plans/p0-lua-emitter-guide-cleanup.md](../plans/p0-lua-emitter-guide-cleanup.md)

1. [x] [ID: P0-LUA-EMITGUIDE-S1] import skip / built-in module skip の hardcode を emitter から外す（2026-04-10）— `typing` / `__future__` / `dataclasses` の `ImportFrom` 直判定と `pytra.built_in.*` prefix 判定を削除し、`should_skip_module(...)` に一本化
2. [x] [ID: P0-LUA-EMITGUIDE-S2] `pytra_isinstance` を emitter 直生成から runtime helper へ戻す（2026-04-10）— `py_runtime.lua` に常設し、module header / `type_id_table` special-case emit を削除
3. [x] [ID: P0-LUA-EMITGUIDE-S3] Lua parity を再確認して task を完了化する（2026-04-10）— guide cleanup に関係する representative fixture / sample / stdlib を再確認

### P0-LUA-NEW-FIXTURE-PARITY: 新規追加 fixture / stdlib の parity 確認

今セッション（2026-04-01〜05）で追加・更新した fixture と stdlib の parity を確認する。

対象: `bytes_copy_semantics`, `negative_index_comprehensive`, `negative_index_out_of_range`, `callable_optional_none`, `str_find_index`, `eo_extern_opaque_basic`(emit-only), `math_extended`(stdlib), `os_glob_extended`(stdlib)

1. [x] [ID: P0-LUA-NEWFIX-S1] 上記 fixture/stdlib の parity を確認する（対象 fixture のみ実行）（2026-04-10）— `bytes_copy_semantics`, `negative_index_comprehensive`, `negative_index_out_of_range`, `callable_optional_none`, `str_find_index`, `eo_extern_opaque_basic`(emit-only), `math_extended`, `os_glob_extended` を確認し、対象 8 件すべて PASS。途中で `bytearray.append` の receiver 補完漏れにより `bytes_copy_semantics` が落ちていたため、Lua emitter の mapped container call で `__BYTEARRAY_*` にも owner 注入を揃えて修正した。

### P0-LUA-TYPE-ID-CLEANUP: Lua runtime から __pytra_isinstance を削除する

仕様: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md) §6

このタスクは 2026-04-10 の guide cleanup で実質 superseded。runtime helper 削除ではなく、emitter 直生成をやめて runtime 常設 helper に戻す方針へ変更した。

1. [x] [ID: P0-LUA-TYPEID-CLN-S1] `src/runtime/lua/built_in/py_runtime.lua` から `__pytra_isinstance` を削除する（2026-04-02）— metatable/type-id 判定 helper は emitter 生成の `pytra_isinstance(...)` に移設
2. [x] [ID: P0-LUA-TYPEID-CLN-S2] fixture + sample parity に回帰がないことを確認する（2026-04-10）— `P0-LUA-EMITGUIDE-S3` で guide cleanup 後の parity を再確認し、runtime helper 常設へ戻した状態でも無回帰を確認

### P1-LUA-EMITTER: Lua emitter を toolchain2 に新規実装する

文脈: [docs/ja/plans/p1-lua-emitter.md](../plans/p1-lua-emitter.md)

1. [x] [ID: P1-LUA-EMITTER-S1] `src/toolchain2/emit/lua/` に Lua emitter を新規実装する — CommonRenderer + override 構成。旧 `src/toolchain/emit/lua/` と TS emitter を参考にする。Lua 固有（1-based index、nil、metatables 等）だけ override（2026-04-01）
2. [x] [ID: P1-LUA-EMITTER-S2] `src/runtime/lua/mapping.json` を作成する — `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` を定義（2026-04-01）
3. [x] [ID: P1-LUA-EMITTER-S3] fixture 全件の Lua emit 成功を確認する（2026-04-01）— `_transpile_in_memory(..., target='lua')` で fixture 136/136 emit success
4. [x] [ID: P1-LUA-EMITTER-S4] Lua runtime を toolchain2 の emit 出力と整合させる（2026-04-01）— Path/json/sys/png/glob/deque/ArgumentParser、class 継承、list/bytearray/string method、linked `pytra_isinstance` を整合
5. [ ] [ID: P1-LUA-EMITTER-S5] fixture + sample の Lua run parity を通す（`lua5.4`）— 2026-04-10 時点で full fixture は `153/153 pass` を再確認。sample は `01_mandelbrot`, `02_raytrace_spheres`, `03_julia_set`, `04_orbit_trap_julia`, `05_mandelbrot_zoom`, `17_monte_carlo_pi`, `18_mini_language_interpreter` を再確認し、historical に `06_julia_parameter_sweep`, `07_game_of_life_loop`, `08_langtons_ant` も `--cmd-timeout-sec 14400` で parity PASS 済み。pure-Python generated helper の load を emitter guide に沿って修正し、`pytra.utils.png/gif` を `dofile()` で接続。`bytearray.extend` と `dict.clear()` を runtime/emitter に追加して full fixture を通し、さらに `static_cast` を `__pytra_int/__pytra_float/...` に戻して `02_raytrace_spheres` / `04_orbit_trap_julia` の artifact mismatch を解消し、今回 `__BYTEARRAY_*` の receiver 補完漏れも修正した。sample full の最新 pass 数は引き続き未確定
6. [x] [ID: P1-LUA-EMITTER-S6] stdlib の Lua parity を通す（`--case-root stdlib`）（2026-04-01）— `runtime_parity_check_fast.py --targets lua --case-root stdlib` で `16/16 pass`

### P3-COPY-ELISION: EAST3 に copy elision メタデータを追加し Lua の bytes コピーを最適化する

文脈: [docs/ja/plans/p3-copy-elision-east-meta.md](../plans/p3-copy-elision-east-meta.md)

`bytes(bytearray)` のコピーが GIF sample の hot path。emitter 独自判断でのコピー省略はセマンティクス違反（差し戻し済み）。linker の解析結果を `copy_elision_safe_v1` として EAST3 meta に載せ、emitter はそのフラグを見てのみ省略する。

1. [x] [ID: P3-COPY-ELISION-S1] `copy_elision_safe_v1` スキーマを spec-east.md に定義する（2026-04-02）— `Call.meta.copy_elision_safe_v1` を canonical linker metadata として定義
2. [x] [ID: P3-COPY-ELISION-S2] linker の def-use / non-escape 解析で copy elision 判定を実装する（2026-04-02）— v1 は narrow/fail-closed。`return bytes(local_bytearray)` が readonly `list[bytes]` フローにしか流れない場合だけ annotate
3. [x] [ID: P3-COPY-ELISION-S3] Lua emitter で `copy_elision_safe_v1` を参照してコピー省略を実装する（2026-04-02）— `__pytra_bytes_alias()` を導入し、metadata がある `bytes(bytearray)` だけ alias 化
4. [ ] [ID: P3-COPY-ELISION-S4] `07_game_of_life_loop` の Lua parity PASS + 性能改善を確認する — `03_julia_set` は無回帰 PASS。2026-04-10 に linker の final row 再 annotation と Lua emitter の `core.bytes_ctor` fast path を修正し、`render()` の `return bytes(frame)` は `__pytra_bytes_alias(frame)` へ実際に切り替わる状態まで確認した。さらに readonly subscript owner を copy-elision 判定に含めて `pytra.utils.gif._lzw_encode()` の `return bytes(out)` も `__pytra_bytes_alias(out)` へ切り替えた。残りは cross-module の `grayscale_palette()` と `f.write(bytes(out))` で、`07_game_of_life_loop` の `--cmd-timeout-sec 600` 完走確認は継続

### P20-LUA-SELFHOST: Lua emitter で toolchain2 を Lua に変換し実行できるようにする

1. [ ] [ID: P20-LUA-SELFHOST-S0] selfhost 対象コードの型注釈補完（他言語と共通）
2. [ ] [ID: P20-LUA-SELFHOST-S1] toolchain2 全 .py を Lua に emit し、実行できることを確認する
3. [ ] [ID: P20-LUA-SELFHOST-S2] selfhost 用 Lua golden を配置する
4. [ ] [ID: P20-LUA-SELFHOST-S3] `run_selfhost_parity.py --selfhost-lang lua --emit-target lua --case-root fixture` で fixture parity PASS
5. [ ] [ID: P20-LUA-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang lua --emit-target lua --case-root sample` で sample parity PASS
