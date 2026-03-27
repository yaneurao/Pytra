<a href="../../ja/plans/archive/20260308-p1-jsonvalue-decode-first-contract.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260308-p1-jsonvalue-decode-first-contract.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260308-p1-jsonvalue-decode-first-contract.md`

# P1: `JsonValue` decode-first 契約と dynamic helper 退役

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-JSONVALUE-DECODE-FIRST-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [spec-linker.md](../spec/spec-linker.md)
- [spec-template.md](../spec/spec-template.md)
- [p2-runtime-sot-linked-program-integration.md](./p2-runtime-sot-linked-program-integration.md)
- [p2-runtime-helper-generics-under-linked-program.md](./p2-runtime-helper-generics-under-linked-program.md)

背景:
- 2026-03-08 時点の `json.loads()` は実装上 `object` を返す経路が残っている。
- その結果、`sum(object)` や `zip(object, object)` のような dynamic helper fallback を runtime に残す誘惑が生まれ、`native/core/py_runtime.h` の縮退を阻害する。
- しかし Pytra は静的型付けを前提にしており、`object` 値のまま built-in や collection helper を適用できる必要は本質的にない。
- JSON の動的性は一般 `object` 問題ではなく、`null/bool/int/float/str/object/array` という JSON 固有の代数的データ型の問題である。
- したがって、`json` 由来の動的境界は `JsonValue` / `JsonObj` / `JsonArr` の専用 surface へ閉じ込め、user-facing dynamic helper を compile error へ寄せる方が設計として一貫する。

目的:
- `json.loads()` とその decode 経路を、一般 `object` ではなく `JsonValue` 系の共通ADTとして定義する。
- `object` に対する dynamic built-in / collection helper fallback を user-facing surface から退役させる。
- JSON の decode-first 契約を導入し、`py_runtime.h` の dynamic helper debt を縮退しやすくする。
- C++ だけでなく、Rust / Swift / Nim など GC なし静的型付け target でも成立する carrier 設計を揃える。

対象:
- `src/pytra/std/json.py` の public surface 再設計
- `JsonValue` / `JsonObj` / `JsonArr` の仕様
- `object` 引数の built-in / collection helper 禁止規約
- JSON decode helper / wrapper API
- backend ごとの carrier 方針
- representative runtime / parity / docs

非対象:
- general-purpose `cast` 機能の language-wide 導入
- `cast_or_raise` のような例外ベース decode
- Python pattern matching の全面実装
- `object` runtime 自体の即時撤去
- JSON 以外の dynamic data source 全般を 1 回で整理すること

受け入れ基準:
- `JsonValue` / `JsonObj` / `JsonArr` の canonical contract が docs/spec 上で固定される。
- `json.loads()` 系の長期正規形が一般 `object` ではなく JSON 専用 surface であることが明文化される。
- `sum(object)` / `zip(object, object)` / `sorted(object)` / object overload の `dict.keys/items/values` は user-facing compile error へ寄せる方針が固定される。
- JSON decode は wrapper/decode API を通す前提になり、dynamic helper を増やす理由として扱わない。
- backend lowering は「各言語で tagged union / enum / variant / wrapper に落とす」共通方針で整理される。

依存関係:
- `P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01` は完了済みとする。
- `P2 runtime SoT linked-program integration` は将来の本命だが、本計画はそれに先行して JSON dynamic boundary の contract を固定してよい。
- `@template` / linked-program specialization は JSON wrapper の generic helper へ将来流用できるが、本計画の必須前提ではない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_runtime_cpp_layout.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_*json*.py'`

## 1. 問題の本質

問題は `json.loads()` が動的であることではなく、その動的性が一般 `object` helper へ漏れていることである。

JSON は実際には次の 7 分岐しか持たない。

- `null`
- `bool`
- `int`
- `float`
- `str`
- `object`
- `array`

したがって必要なのは general dynamic helper ではなく、JSON 専用の decode surface である。

## 2. 基本方針

1. `json.loads()` の長期正規形は `JsonValue` とする。
2. `JsonObj` は意味論上 `dict[str, JsonValue]`、`JsonArr` は意味論上 `list[JsonValue]` とする。
3. user code は `JsonValue` 系 decode API を通して concrete type を得てから built-in / operator を使う。
4. `object` 値を built-in / collection helper に直接渡す経路は compile error とし、dynamic helper fallback で救済しない。
5. backend は `JsonValue` を target ごとに idiomatic な tagged union / enum / variant / wrapper へ lower する。
6. 一時的に `object` を内部 carrier に使う実装は許容してよいが、user-facing surface には露出しない。

## 3. 想定する public surface

長期正規形:

- `json.loads(text: str) -> JsonValue`
- `json.loads_obj(text: str) -> JsonObj | None`
- `json.loads_arr(text: str) -> JsonArr | None`

`JsonValue`:

- `as_obj() -> JsonObj | None`
- `as_arr() -> JsonArr | None`
- `as_str() -> str | None`
- `as_int() -> int | None`
- `as_float() -> float | None`
- `as_bool() -> bool | None`

`JsonObj`:

- `get(key: str) -> JsonValue | None`
- `get_obj(key: str) -> JsonObj | None`
- `get_arr(key: str) -> JsonArr | None`
- `get_str(key: str) -> str | None`
- `get_int(key: str) -> int | None`
- `get_float(key: str) -> float | None`
- `get_bool(key: str) -> bool | None`

`JsonArr`:

- `get(index: int) -> JsonValue | None`
- `get_obj(index: int) -> JsonObj | None`
- `get_arr(index: int) -> JsonArr | None`
- `get_str(index: int) -> str | None`
- `get_int(index: int) -> int | None`

補足:

- exact API 名は実装時に微調整してよい。
- 重要なのは `cast` 一般論ではなく、JSON 専用 wrapper/decode API に閉じること。

## 4. backend carrier 方針

- C++:
  - `std::variant` または nominal wrapper
- Rust:
  - `enum JsonValue`
- Swift:
  - `indirect enum JsonValue`
- Nim:
  - tagged union / `ref object`

共通ルール:

- `JsonValue` は target 非依存の共通ADTとして先に定義する。
- `object` は fallback carrier として内部で使ってよいが、public contract をそれに引きずらせてはならない。
- JSON のためだけに `sum(object)` のような helper を backend/runtime へ追加してはならない。

## 5. 段階導入

### Phase 1: inventory と契約固定

- `json.loads()->object` に依存している surface を棚卸しする。
- `spec-runtime` / `spec-dev` に `JsonValue` と decode-first 契約を固定する。
- dynamic helper compile error の対象を列挙する。

### Phase 2: surface 設計

- `JsonValue` / `JsonObj` / `JsonArr` の nominal type surface を決める。
- `loads_obj` / `loads_arr` を含む decode API を固める。
- `match` / narrowing / future cast の関係を整理する。

### Phase 3: backend carrier / runtime 実装

- C++ / Rust / Swift / Nim を優先に carrier を決める。
- `std/json` runtime と parity suite を追従させる。
- `object` fallback helper の削除または internal 化を進める。

### Phase 4: cleanup と guard

- `py_runtime.h` / runtime layout guard に dynamic helper 再侵入防止を追加する。
- representative parity を固定する。
- docs を同期して本計画を閉じる。

## 6. タスク分解

- [ ] [ID: P1-JSONVALUE-DECODE-FIRST-01] JSON の動的境界を `JsonValue` 系へ閉じ込め、`object` 向け dynamic helper を user-facing surface から退役させる。
- [ ] [ID: P1-JSONVALUE-DECODE-FIRST-01-S1-01] `json.loads()->object` と `sum/zip/sorted/keys/items/values(object)` の依存箇所を棚卸しする。
- [ ] [ID: P1-JSONVALUE-DECODE-FIRST-01-S1-02] `spec-runtime` / `spec-dev` に `JsonValue` 共通ADTと decode-first 契約を固定する。
- [ ] [ID: P1-JSONVALUE-DECODE-FIRST-01-S2-01] `JsonValue` / `JsonObj` / `JsonArr` の public surface と `loads_obj` / `loads_arr` の exact API を決める。
- [ ] [ID: P1-JSONVALUE-DECODE-FIRST-01-S2-02] `object` 型を built-in / collection helper へ直接渡したとき compile error とする validator/guard 方針を固定する。
- [ ] [ID: P1-JSONVALUE-DECODE-FIRST-01-S3-01] C++ / Rust / Swift / Nim の carrier 方針を具体化し、実装優先順を決める。
- [ ] [ID: P1-JSONVALUE-DECODE-FIRST-01-S3-02] `std/json` runtime と representative decode path を `JsonValue` surface へ寄せる最初の実装 slice を入れる。
- [ ] [ID: P1-JSONVALUE-DECODE-FIRST-01-S4-01] dynamic helper debt の guard と representative parity を固定する。
- [ ] [ID: P1-JSONVALUE-DECODE-FIRST-01-S4-02] docs / decision log / archive 同期まで完了し、本計画を閉じる。

## 7. 決定ログ

- 2026-03-08: JSON のために language-wide dynamic helper を維持しない。動的性は `JsonValue` 系の専用 surface に閉じ込める方針を採る。
- 2026-03-08: `sum(object)` / `zip(object, object)` のような helper は permanent API にせず、compile error へ寄せる target design とする。
- 2026-03-08: general-purpose `cast_or_raise` は JSON decode には採用しない。必要な decode は JSON module 専用 wrapper/decode API に寄せる。
- 2026-03-08: 各 backend での carrier は target idiom に従うが、共通意味論は `JsonValue` という target 非依存ADTで先に固定する。
- 2026-03-08: `JsonValue.Int` の payload は `int64`、`JsonValue.Float` の payload は `float64` とする。JSON number のうち小数点/exponent を含まないものは `Int(int64)`、含むものは `Float(float64)` として解釈し、`int64` 範囲外整数は parse error とする。
- 2026-03-08: `json` は stdlib compatibility family に属するため、decode-first 契約を持っても public module root は `pytra.std.json` のまま維持する。`pytra.utils.json` への移設は行わない。
- 2026-03-08 [ID: P1-JSONVALUE-DECODE-FIRST-01-S1-01]: `json.loads()->object` 依存の第一群は `src/py2x.py`, `src/toolchain/link/program_loader.py`, `src/toolchain/link/link_manifest_io.py`, `src/toolchain/link/materializer.py`, `src/toolchain/ir/east_io.py` の JSON file loader で、いずれも `payload_any = json.loads(...)` から raw `dict[str, object]` tree を組み立てている。selfhost 側の本丸は別 P2 (`P2-JSONVALUE-SELFHOST-ALIGN-01`) に分離し、この P1 では `pytra.std.json` contract と user-facing dynamic helper 退役を先に固定する。
- 2026-03-08 [ID: P1-JSONVALUE-DECODE-FIRST-01-S1-01]: dynamic helper debt の代表は `src/runtime/cpp/native/core/py_runtime.h` の `sum(const object&)`, `zip(const object&, const object&)`, `py_dict_keys(const object&)`, `py_dict_items(const object&)`, `py_dict_values(const object&)` と、SoT 側 `src/pytra/built_in/contains.py`, `src/pytra/built_in/iter_ops.py` の object helper (`py_contains_*_object`, `py_reversed_object`, `py_enumerate_object`) である。compile error 対象の中心は `sum/zip/sorted/keys/items/values(object)` で、`contains/reversed/enumerate(object)` は後続 tranche で同じ方針へ寄せる。
- 2026-03-08 [ID: P1-JSONVALUE-DECODE-FIRST-01-S1-01]: `src/pytra/std/json.py` 自体も現状は `loads(text) -> object`, `_parse_object() -> dict[str, object]`, `_parse_array() -> list[object]`, `_parse_number() -> object` で raw object tree を返している。したがって P1 の主作用点は (1) `pytra.std.json` の public surface を `JsonValue` / `JsonObj` / `JsonArr` へ置き換えること、(2) user-facing dynamic helper fallback を permanent API にしないこと、の 2 点とする。
- 2026-03-08 [ID: P1-JSONVALUE-DECODE-FIRST-01-S1-02]: `spec-runtime` では `JsonValue` 共通ADT、`pytra.std.json` root 維持、`sum(object)` / `zip(object, object)` / object overload の `dict.keys/items/values` を permanent API にしないこと、JSON number の `int64` / `float64` 幅まで固定済みであることを確認した。`spec-dev` でも `object` 値を built-in / collection helper へ直接渡すのは compile error を正とし、`json.loads()` 由来値は `JsonValue` decode surface で concrete type へ落としてから使う契約が入っているため、S1-02 の docs fix は受理条件を満たしている。
- 2026-03-08 [ID: P1-JSONVALUE-DECODE-FIRST-01-S2-01]: `spec-runtime` の decode surface を v1 canonical API として固定した。`loads`, `loads_obj`, `loads_arr`, `JsonValue.as_*`, `JsonObj.get_*`, `JsonArr.get_*` を exact 名とし、`JsonArr` 側も `get_obj/get_arr/get_str/get_int/get_float/get_bool` まで揃えて `JsonObj` と対称にした。v1 は general-purpose `cast` や `match` を前提にせず、この helper surface だけで JSON decode を完結させる。
- 2026-03-08 [ID: P1-JSONVALUE-DECODE-FIRST-01-S2-02]: validator/guard の責務は frontend/lowering を正本にすると固定した。`sum/zip/sorted/min/max/keys/items/values` へ `object` / `Any` / `unknown` が直接入る呼び出しは `Call` rewrite 前後で compile error にし、emit 時は fail-fast guard のみ許可する。backend/runtime が dynamic fallback helper を暗黙挿入して救済する設計は採らない。
- 2026-03-08 [ID: P1-JSONVALUE-DECODE-FIRST-01-S3-01]: backend carrier の v1 具体案と優先順を固定した。実装順は `C++ -> Rust -> Swift -> Nim` とし、C++ は `class JsonValue` + `std::variant<monostate,bool,int64,float64,str,rc<JsonObj>,rc<JsonArr>>`、Rust は `enum JsonValue`、Swift は `indirect enum JsonValue`、Nim は `kind` discriminator を持つ `ref object` tagged union を正本とする。`object` / `dict[str, object]` / `list[object]` は内部 detail としてのみ一時許容し、public surface には昇格させない。
- 2026-03-08 [ID: P1-JSONVALUE-DECODE-FIRST-01-S3-02]: first implementation slice は `JsonValue` / `JsonArr` を一気に nominal 化せず、`pytra.std.json` に `loads_obj(text) -> JsonObj | None` と `JsonObj.get_obj/get_arr/get_str/get_int/get_float/get_bool` を追加する compatibility lane から入れた。`loads(text) -> object` は既存 selfhost / host loader 互換のため当面残し、`JsonValue` 本体と `loads_arr` / `JsonArr` の nominal wrapper は後続 tranche へ残す。
- 2026-03-08 [ID: P1-JSONVALUE-DECODE-FIRST-01-S3-02]: C++ runtime は `std/json` の checked-in generated artifact をこの first slice に追従させ、`JsonObj.get_int/get_float/get_bool` は `return raw;` ではなく `int(raw) / float(raw) / bool(raw)` へ明示変換して `py_to_*` lowering を得る形に固定した。`str.join(rc<list<str>>)` 不整合は `_join_strs(parts, sep)` helper を `json.py` 側へ置いて回避し、`test_pylib_json.py` と `test_py2cpp_features.py -k json` を green にして representative path を固定した。
- 2026-03-08 [ID: P1-JSONVALUE-DECODE-FIRST-01-S4-01]: frontend/lowering に decode-first guard を追加し、`sum/zip/min/max/sorted` へ `object` / `Any` / `unknown` を直接渡す呼び出しと、`keys/items/values` を同じ動的 receiver に対して呼ぶ経路を `unsupported_syntax` で fail-fast させた。実装は `src/toolchain/ir/core.py` の `_guard_dynamic_helper_args` / `_guard_dynamic_helper_receiver` で行い、`test_east_core.py` と `test_py2cpp_features.py` に `json.loads(...)->sum/zip/keys` が C++ emit 前に落ちる regression を追加した。
- 2026-03-08 [ID: P1-JSONVALUE-DECODE-FIRST-01-S4-01]: runtime debt の snapshot は `test_cpp_runtime_iterable.py` で固定した。typed `sum/min/max/zip` は generated helper へ移ったまま `py_runtime.h` に戻らず、残っている object overload debt (`py_dict_keys/items/values(object)`, `zip(object, object)`, `sum(object)`) だけが visible であることを回帰化した。代表確認は `test_pylib_json.py`, `test_east_core.py`, `test_py2cpp_features.py`, `test_cpp_runtime_iterable.py`, `runtime_parity_check.py --targets cpp --case-root fixture`、および sample parity の C++ lane で行う。
