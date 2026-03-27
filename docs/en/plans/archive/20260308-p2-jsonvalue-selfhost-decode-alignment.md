<a href="../../ja/plans/archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md`

# P2: `JsonValue` を使った selfhost JSON 境界の整列

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-JSONVALUE-SELFHOST-ALIGN-01`

関連:
- [p1-jsonvalue-decode-first-contract.md](./p1-jsonvalue-decode-first-contract.md)
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [spec-tools.md](../spec/spec-tools.md)

背景:
- `JsonValue` 導入後も、selfhost/host 境界の JSON artifact loader が `dict[str, object]` / `list[object]` / `object` のままだと、user-facing dynamic helper を退役させても bootstrap 経路だけが旧契約に取り残される。
- 現在の JSON artifact 読み込みは `py2x.py`, `py2x-selfhost.py`, `ir2lang.py`, `toolchain/link/program_loader.py`, `toolchain/link/program_validator.py` などで `json.loads()` 後の raw object tree を直接扱っている。
- これらは selfhost 化の都合で pure Python 実装に寄っているが、だからこそ `JsonValue` / `JsonObj` / `JsonArr` の decode helper へ早めに揃えておく価値がある。
- 一方で backend 全体や `tools/` 全体を一度に移行すると blast radius が大きい。まずは「JSON file を読む境界」に限定する方が安全である。

目的:
- selfhost/host の JSON artifact 境界を `JsonValue` decode-first 契約へ揃える。
- `dict[str, object]` / `list[object]` を前提にした loader/validator を、`JsonObj` / `JsonArr` 経由の decode helper ベースへ置き換える。
- selfhost path でも dynamic helper に依存せず、`JsonValue` を使って linked-program / EAST JSON を読める状態にする。
- JSON 専用の動的性を `pytra.std.json` の surface に閉じ込め、`object` 一般論へ広げない。

対象:
- `src/pytra/std/json.py`
- `src/py2x.py`
- `src/py2x-selfhost.py`
- `src/ir2lang.py`
- `src/toolchain/link/program_loader.py`
- `src/toolchain/link/program_validator.py`
- representative selfhost / linked-program / CLI tests
- docs / tooling contract

非対象:
- backend emitter 全体の `object` 整理
- `tools/` 配下の全 JSON loader 一括移行
- Python `match` 構文の全面サポート
- language-wide `cast` 機能
- JSON 以外の dynamic source 全般の整理

受け入れ基準:
- selfhost/host の主要 JSON artifact 読み込み経路が `JsonValue` decode helper を使う。
- `py2x-selfhost.py` が `json.loads()->object` 依存なしに linked artifact / EAST JSON を扱える。
- `program_loader` / `program_validator` が raw `dict[str, object]` tree を直接前提にしない。
- representative selfhost / linked-program tests が `JsonValue` 経路で green になる。
- docs に「selfhost ではまず JSON 境界を `JsonValue` へ揃え、backend 全体は後続」と明記される。

依存関係:
- `P1-JSONVALUE-DECODE-FIRST-01` の API と number payload 幅が固まっていること。
- `JsonValue` / `JsonObj` / `JsonArr` の public surface が少なくとも P1 の Phase 2 まで進んでいること。
- `match` は前提にしない。v1 は decode helper method (`as_obj`, `get_str`, `get_obj`, など) ベースで進める。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/link -p 'test_*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_ir2lang_cli.py'`
- `python3 tools/check_noncpp_east3_contract.py --skip-transpile`

## 1. 基本方針

1. `json.loads()` の戻り値を直接 `dict[str, object]` と見なさない。
2. まず `JsonValue` として受け、`as_obj()` / `as_arr()` / `get_*()` を通して decode する。
3. selfhost であっても raw object tree の「手探り読み」を増やさない。
4. v1 では `match` や general `cast` に頼らず、JSON module 専用 helper だけで完結させる。
5. backend 全体や `tools/` 全体は後続計画に分離し、この計画は JSON artifact 境界に限定する。

## 2. 優先移行対象

第一優先:
- `src/pytra/std/json.py`
- `src/toolchain/link/program_loader.py`
- `src/toolchain/link/program_validator.py`

第二優先:
- `src/py2x.py`
- `src/py2x-selfhost.py`
- `src/ir2lang.py`

後続:
- `tools/` 配下の JSON loader
- backend/runtime parity 補助スクリプト

### 2.1 inventory（2026-03-08）

- host / selfhost 共通の raw JSON artifact 境界
  - `src/py2x.py`
    - `_load_json_root()` が `json.loads() -> dict[str, object]` を前提に root copy を行う。
    - linked-program restart (`--from-link-output`) と JSON input restart がこの lane を通る。
  - `src/ir2lang.py`
    - `_load_json_root()` が raw dict root を前提にし、`_unwrap_east_module()` が `{"ok": true, "east": {...}}` または `{"kind": "Module", ...}` を `isinstance(..., dict)` で手探り decode している。
  - `src/toolchain/ir/east_io.py`
    - `.json` 入力時に `json.loads()` 後の raw dict / wrapper payload を直接判定して `EAST Module` へ正規化している。
- linked-program manifest / bundle lane
  - `src/toolchain/link/program_loader.py`
    - `_load_raw_east3()` が raw dict copy を行い、`build_linked_program_from_module_map()` も `dict[str, object]` 前提のまま module map を組み立てる。
  - `src/toolchain/link/program_validator.py`
    - `_require_dict/_require_str/_require_bool/_require_str_list()` が raw object tree 前提で manifest / linked output を検証している。
  - `src/toolchain/link/link_manifest_io.py`
    - `_load_json_doc()` が raw dict root を返してから validator へ渡す。
  - `src/toolchain/link/materializer.py`
    - `_load_json_doc()` / `_load_linked_east3_doc()` が raw dict root 前提で linked bundle を読む。
- selfhost 導線の現状
  - `src/py2x-selfhost.py` 自体は `json.loads()` を直接呼ばない。
  - ただし `toolchain.compiler.transpile_cli.load_east3_document()` と linked-program restart 導線に依存するため、`py2x.py` / `ir2lang.py` / `east_io.py` / `toolchain/link/*` を `JsonValue` lane に揃えることが selfhost 整列の実体になる。
  - `py2x-selfhost.py` 内の `dict[str, object]` は backend spec / layer option の内部 carrier であり、本計画の JSON artifact 境界とは別扱いにする。

## 3. 想定する decode 形

避けたい形:

```python
payload_any = json.loads(text)
if not isinstance(payload_any, dict):
    ...
doc: dict[str, object] = payload_any
```

寄せたい形:

```python
payload = json.loads(text)
doc = payload.as_obj()
if doc is None:
    ...
schema = doc.get_str("schema")
modules = doc.get_arr("modules")
```

または:

```python
root = json.loads_obj(text)
if root is None:
    ...
entry_modules = root.get_arr("entry_modules")
```

## 4. 段階導入

### Phase 1: inventory と契約固定

- selfhost/host の JSON loader で `dict[str, object]` / `list[object]` を直接前提にしている箇所を棚卸しする。
- `JsonValue` 導入後も selfhost は decode helper ベースで進めると docs に固定する。

### Phase 2: JSON surface の selfhost-ready 化

- `pytra.std.json` に selfhost でも使える `JsonValue` / `JsonObj` / `JsonArr` surface を追加する。
- `loads_obj` / `loads_arr` など、境界コードが短く書ける API を最小セットで入れる。

### Phase 3: loader / validator 移行

- `program_loader` / `program_validator` を `JsonValue` decode ベースへ移行する。
- `py2x.py` / `py2x-selfhost.py` / `ir2lang.py` も同じ decode lane へ揃える。

### Phase 4: regression / guard / docs cleanup

- representative tests を `JsonValue` decode lane へ更新する。
- 旧 raw object tree 依存が再侵入しない guard を検討する。
- docs と決定ログを同期して閉じる。

## 5. タスク分解

- [ ] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01] `JsonValue` を使って selfhost/host の JSON artifact 境界を decode-first 契約へ揃える。
- [ ] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S1-01] selfhost/host の JSON loader で `dict[str, object]` / `list[object]` を直接前提にしている箇所を棚卸しする。
- [ ] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S1-02] docs に「selfhost は `match` ではなく decode helper ベースで `JsonValue` を使う」契約を固定する。
- [ ] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S2-01] `pytra.std.json` に selfhost-ready な `loads_obj` / `loads_arr` / `JsonObj.get_*` 最小APIを定義する。
- [ ] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S2-02] `program_loader` / `program_validator` の JSON decode を `JsonValue` helper ベースへ移行する。
- [ ] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S3-01] `py2x.py` / `py2x-selfhost.py` / `ir2lang.py` の JSON artifact 境界を `JsonValue` decode lane へ揃える。
- [ ] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S3-02] representative selfhost / linked-program / CLI tests を `JsonValue` 経路で green にする。
- [ ] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S4-01] raw object tree 依存の再侵入を防ぐ guard / regression を追加する。
- [ ] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S4-02] docs / decision log / archive 同期まで完了し、本計画を閉じる。

## 6. 決定ログ

- 2026-03-08: selfhost も `JsonValue` へ揃える。ただし backend 全体ではなく、まず JSON artifact を読む境界に限定する。
- 2026-03-08: selfhost 側の v1 は `match` 前提にしない。`JsonValue` / `JsonObj` / `JsonArr` の decode helper method だけで進める。
- 2026-03-08: `pytra.std.json` の public root は維持し、selfhost 対応のために `utils/json.py` へは移さない。
- 2026-03-08: inventory の結果、priority は `program_loader/program_validator/link_manifest_io/materializer` と `py2x/ir2lang/east_io` の 2 群に分かれる。`py2x-selfhost.py` 本体は raw JSON parse を持たず、selfhost alignment は周辺 decode lane の整列で達成する。
- 2026-03-08: `S2-01` では `loads_obj` に加えて `loads_arr`, `JsonValue.as_*`, `JsonObj.get/get_*`, `JsonArr.get/get_*` を実装した。`loads()` 自体は互換のため raw `object` 戻り値を維持し、selfhost 境界は専用 helper を使って decode する。
- 2026-03-08: `JsonObj` / `JsonArr` / `JsonValue` の相互参照を checked-in C++ runtime へ落とすため、`header_builder` は class block の前に forward declaration を出す形へ修正した。
- 2026-03-08: `S2-02` では `program_loader` / `program_validator` / `link_manifest_io` / `materializer` の root decode を `json.loads_obj()` へ寄せ、validator の内部正規形を `JsonObj` / `JsonArr` に切り替えた。外向けの return contract は `dict[str, object]` / `Link*Entry` のまま維持し、call site を一度に壊さない形に留めた。
- 2026-03-08: `S3-01` では `py2x.py` の link-input 判定を `JsonObj.get_str("schema")` ベースへ、`ir2lang.py` と `toolchain/ir/east_io.py` の wrapped/root unwrap を `loads_obj()` / `JsonObj.get_*` ベースへ切り替えた。`py2x-selfhost.py` 本体は raw JSON parse を持たないため変更不要と判断した。
- 2026-03-08: `S3-02` の代表確認として `test_py2x_cli.py`, `test_ir2lang_cli.py`, `test_pylib_json.py`, `test/unit/link/test_*.py`, `check_noncpp_east3_contract.py --skip-transpile` を実行し、`JsonValue` decode lane で green を確認した。
- 2026-03-08: `S4-01` では `tools/check_jsonvalue_decode_boundaries.py` と `test_check_jsonvalue_decode_boundaries.py` を追加し、`py2x` / `ir2lang` / `east_io` / `toolchain/link/*` の JSON artifact 境界が `json.loads_obj(...)` を正本に保ち、raw `json.loads(...)` を再侵入させない guard を local CI (`tools/run_local_ci.py`) に常設した。
- 2026-03-08: `S4-02` では `spec-tools` / `how-to-use` を guard 運用へ同期し、本計画を archive へ移せる状態で閉じた。
