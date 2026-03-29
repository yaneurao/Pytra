<a href="../../ja/plans/archive/20260308-p3-compiler-jsonvalue-internal-alignment.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260308-p3-compiler-jsonvalue-internal-alignment.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260308-p3-compiler-jsonvalue-internal-alignment.md`

# P3: compiler/backend 内部 JSON 読み込みを `JsonValue` に揃える

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P3-COMPILER-JSONVALUE-INTERNAL-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [spec-tools.md](../spec/spec-tools.md)
- [archive/20260308-p1-jsonvalue-decode-first-contract.md](./archive/20260308-p1-jsonvalue-decode-first-contract.md)
- [archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md](./archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md)

背景:
- `JsonValue` / `JsonObj` / `JsonArr` と decode-first 契約は、JSON artifact 境界では既に導入済みである。
- しかし compiler/backend 内部にはまだ `json.loads(...)` で raw `dict[str, object]` を読む host path が残っている。
- 代表例は `backends/common/emitter/code_emitter.py`, `toolchain/frontends/transpile_cli.py`, `toolchain/frontends/runtime_symbol_index.py`, `backends/js/emitter/js_emitter.py` であり、selfhost を常用導線に戻す前にこのズレを減らしたい。
- いま残っている raw-dict lane は user-facing dynamic helper とは別だが、compiler 自身が `object` / `dict[str, object]` に依存し続けると、selfhost 時に host-only fallback が再侵入しやすい。

目的:
- compiler/backend 内部で JSON file / profile / symbol index を読む経路を `JsonObj` / `JsonArr` ベースへ揃える。
- host path と selfhost path の JSON decode 契約をそろえ、`json.loads(...) -> raw dict` のばらつきを減らす。
- selfhost 化の前段として「変換器本体の JSON 利用は `JsonValue` decode-first」を current contract にする。

対象:
- `src/backends/common/emitter/code_emitter.py`
- `src/toolchain/frontends/transpile_cli.py`
- `src/toolchain/frontends/runtime_symbol_index.py`
- `src/backends/js/emitter/js_emitter.py`
- 必要なら関連する lightweight profile / metadata loader
- representative tests
- docs / guard

非対象:
- `pytra.std.json` 自体の carrier redesign
- `JsonValue.raw` / `JsonObj.raw` / `JsonArr.raw` の廃止
- generated C++ runtime `json.h/json.cpp` の nominal carrier 化
- compiler/backend の内部辞書型（`dict[str, object]` で保持する IR/options/state）の全面廃止
- `make_object` / `py_to<T>(object)` / `type_id` の runtime core 整理

受け入れ基準:
- 上記対象の raw `json.loads(...)` 呼び出しが `loads_obj()` / `loads_arr()` ベースへ移行している。
- JSON root の kind / schema / include fragment 判定が `JsonObj.get_*` ベースで行われる。
- selfhost で通す compiler/backend path に host-only raw JSON decode が残らない。
- representative tests と guard が green になる。
- docs に「artifact 境界だけでなく compiler/backend 内部 JSON loader も `JsonValue` 正本」と明記される。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `git diff --check`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_ir2lang_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_runtime_symbol_index.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/backends -p 'test_*js*'`

## 1. 基本方針

1. `json.loads(...)` の戻り値を `dict` / `list` と見なす host-side convenience を増やさない。
2. root 判定は `loads_obj()` / `loads_arr()` と `JsonObj.get_*` / `JsonArr.get_*` で行う。
3. `dict[str, object]` への変換は「decode 完了後の内部保持」に限定し、JSON parse 直後の raw tree を握らない。
4. selfhost 復旧に必要な compiler/backend 内部 path を優先し、外部 tool 全体の一括移行は後回しにする。

## 2. 優先対象

第一優先:
- `src/toolchain/frontends/transpile_cli.py`
- `src/toolchain/frontends/runtime_symbol_index.py`
- `src/backends/common/emitter/code_emitter.py`

第二優先:
- `src/backends/js/emitter/js_emitter.py`
- 同種の profile / metadata loader

後続:
- `tools/` 配下の host-only JSON helper
- backend ごとの周辺補助スクリプト

## 3. 段階導入

### Phase 1: inventory と契約固定

- compiler/backend 内部で `json.loads(...)` を直接使う箇所を棚卸しする。
- どこまでを selfhost blocker と見なすかを docs に固定する。

### Phase 2: representative host path の置換

- `transpile_cli`, `runtime_symbol_index`, `code_emitter` を `JsonValue` lane へ移す。
- root 判定と dict 化の境界を最小化する。

### Phase 3: backend 補助 path の置換

- `js_emitter` など残る backend internal loader を `JsonValue` lane にそろえる。
- representative regressions を更新する。

### Phase 4: guard / docs / close

- raw `json.loads(...)` 再侵入 guard を追加する。
- docs と archive を同期して閉じる。

## 4. タスク分解

- [ ] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01] compiler/backend 内部の JSON raw-dict loader を `JsonValue` decode-first 契約へ揃える。
- [x] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S1-01] compiler/backend 内部で `json.loads(...)` を直接使う箇所を棚卸しする。
- [x] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S1-02] selfhost blocker と host-only 後回し対象を決定ログへ固定する。
- [x] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S2-01] `transpile_cli.py` の JSON root loader を `loads_obj()` ベースへ移行する。
- [x] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S2-02] `runtime_symbol_index.py` と `code_emitter.py` の JSON loader を `JsonValue` lane へ移行する。
- [x] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S3-01] backend internal loader（`js_emitter.py` など）を `JsonValue` lane へそろえる。
- [x] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S3-02] representative tests / selfhost-related regressions を更新する。
- [x] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S4-01] raw `json.loads(...)` 再侵入 guard を追加する。
- [x] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S4-02] docs / archive を同期して本計画を閉じる。

## 5. 決定ログ

- 2026-03-08: `JsonValue` の artifact 境界導入だけでは不十分で、compiler/backend 内部の host path も `JsonValue` へ寄せないと selfhost で raw-dict fallback が残る。そこで専用の P3 を切って host/selfhost の JSON decode 契約をそろえる。
- 2026-03-08: `src/` 配下で `json.loads(...)` を直接使っていた compiler/backend 内部 path は 4 件に絞れた。`toolchain/frontends/transpile_cli.py` は EAST root unwrap、`toolchain/frontends/runtime_symbol_index.py` は `tools/runtime_symbol_index.json` cache loader、`backends/common/emitter/code_emitter.py` は `profile.json` + include fragment loader、`backends/js/emitter/js_emitter.py` は JS profile loader の private helperで raw dict を握っていた。
- 2026-03-08: selfhost blocker は `transpile_cli.py` と `runtime_symbol_index.py` に固定する。どちらも frontend/common metadata path であり、host/selfhost の decode 契約差分が残ると selfhost 復旧時に raw-dict fallback が再侵入しやすい。
- 2026-03-08: `backends/common/emitter/code_emitter.py` と `backends/js/emitter/js_emitter.py` は host-only follow-up として同じ P3 に残す。JS backend は C++ selfhost の blocker ではないが、common profile loader を `JsonObj` 化しておくと後続 backend へ横展開しやすい。
- 2026-03-08: `transpile_cli.py` の `.json` root unwrap は `json.loads_obj(...)` + `JsonObj.get_bool/get_obj/get_str` に寄せ、`dict[str, object]` 化は wrapper/module 判定後の `east_obj.raw` / `payload.raw` に限定した。これで frontend entrypoint の raw `json.loads(...)` は 1 件減った。
- 2026-03-08: `runtime_symbol_index.py` の cache loader と `CodeEmitter._load_json_dict()` は `json.loads_obj(...)` ベースへ移し、raw root 判定を `JsonObj` に統一した。内部保持は引き続き `dict[str, Any]` だが、parse 直後の raw `json.loads(...)` は消えた。
- 2026-03-08: `js_emitter.py` の private profile loader も `json.loads_obj(...)` ベースへ揃え、`CodeEmitter` と同じ decode-first 境界にそろえた。JS smoke の `load_js_profile()` 回帰と、`CodeEmitter` / `runtime_symbol_index` の non-object root regression を追加して representative coverage を固定した。
- 2026-03-08: `tools/check/check_jsonvalue_decode_boundaries.py` の対象へ `transpile_cli.py` / `runtime_symbol_index.py` / `code_emitter.py` / `js_emitter.py` を追加し、artifact 境界だけでなく compiler/backend 内部 JSON loader も raw `json.loads(...)` 再侵入禁止の対象に広げた。
