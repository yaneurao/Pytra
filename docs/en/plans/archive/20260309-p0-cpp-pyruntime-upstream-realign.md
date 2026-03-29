<a href="../../ja/plans/archive/20260309-p0-cpp-pyruntime-upstream-realign.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-upstream-realign.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-upstream-realign.md`

# P0: C++ `py_runtime.h` の非core helper を削除し、上流 / SoT / 専用laneへ再配置する

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-UPSTREAM-REALIGN-01`

背景:
- `src/runtime/cpp/core/py_runtime.h` 自体は forwarder に縮退済みだが、実体の `src/runtime/cpp/native/core/py_runtime.h` には依然として「core に残す理由が弱い helper」が混在している。
- 問題は header 行数そのものではない。C++ core runtime に不要な helper を抱え込むことで、他 target runtime を書くときにも同種の helper を各言語で再実装・追従させる負担が発生していることが本質である。
- 具体的には、dead include / 未使用 compat shim、C++ emitter 専用の薄い compat helper、generic に見えるが実質単用途の helper、parser/EAST が `pytra.core.py_runtime` へ早期束縛してしまっている built_in helper が混在している。
- たとえば `py_bool_to_string` は C++ emitter の文字列化都合でしかなく、runtime core に置く理由が弱い。`len` bare alias は selfhost 互換の残骸であり、上流 lowering で潰すべきである。generic `getattr(object, name, default)` は現状 `type_id` probe 用途しか見えていない。
- さらに `print` / `ord` / `chr` / `int(x, base)` は parser/EAST が早い段階で `pytra.core.py_runtime` へ束縛しており、C++ だけでなく複数 target runtime 側にも同等 helper を散らしている。これは `py_runtime.h` を削る話であると同時に、上流責務境界の問題でもある。
- したがって本件は「header を分割して見かけの行数を減らす」計画ではなく、「非core helper を delete / inline / upstream lowering / SoT generated / dedicated lane のどこへ送るかを決めて、core から外す」計画として扱う。

目的:
- `src/runtime/cpp/native/core/py_runtime.h` に残る責務を `PyObj` / `object` / `rc<>` / type_id primitive / low-level container primitive / dynamic iteration / process glue に寄せる。
- 現行 tree で不要な helper は削除する。
- runtime core に居る必要がない helper は、優先順に「上流で処理する」「SoT / generated に戻す」「dedicated runtime lane に隔離する」のいずれかへ再配置する。
- 他 target runtime 実装時に「C++ core にあるから同じものを別言語でも増やす」という負債を減らす。

対象:
- `src/runtime/cpp/native/core/py_runtime.h`
- `src/backends/cpp/emitter/*`
- `src/toolchain/ir/core.py`
- 必要に応じて `src/pytra/built_in/*.py`
- 必要に応じて `src/runtime/cpp/generated/built_in/*`
- 必要に応じて他 target runtime の built_in / print / scalar helper 実装
- 関連 test / spec / TODO

非対象:
- `py_runtime.h` の単純な物理分割だけで完了扱いにすること
- `PyObj` / `object` / boxing / unboxing / container primitive の全面刷新
- `scope_exit` / process I/O / dynamic iteration primitive を本件だけで一気に削除すること
- docs/en の先行同期

受け入れ基準:
- `py_runtime.h` から、現行 tree で不要な dead include / 未使用 compat shim が除去される。
- `py_runtime.h` から、C++ emitter 専用 compat helper と判断したものが削除または emitter inline へ置換される。
- `len` bare alias と generic `getattr` について、`core` に残さない形へ置換されるか、少なくとも削除前提の upstream contract が固定される。
- parser/EAST が `print` / `ord` / `chr` / `int(x, base)` を `pytra.core.py_runtime` へ固定束縛する経路が解消される。
- `py_runtime.h` に残る helper は「core runtime に残す理由」を説明できるものに限定される。
- representative C++ backend/runtime test と必要な parity が非退行で通る。
- `tools/check/check_todo_priority.py` が通る。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `rg -n "#include <(cctype|filesystem|fstream|functional|regex|typeinfo)>" src/runtime/cpp/native/core/py_runtime.h`
- `rg -n "\\burllib\\b|urlretrieve" src test sample`
- `rg -n "py_bool_to_string|static inline int64 len\\(|static inline object getattr\\(" src/runtime/cpp/native/core/py_runtime.h`
- `rg -n "pytra\\.core\\.py_runtime" src/toolchain/ir/core.py src/backends/cpp`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_cpp_runtime_*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_*cpp*bridge*.py'`
- `python3 tools/check/runtime_parity_check.py --targets cpp --case-root fixture`

## 優先順位の原則

本件では、helper を次の優先順で扱う。

1. delete
   - 現行 checked-in callsite がなく、存在理由が失われているもの。
2. emitter / lowering inline
   - target runtime に共通化する価値がなく、単に backend 側の描画都合で必要なもの。
3. upstream lowering / EAST contract
   - builtin binding や raw call fallback が原因で runtime へ押し込まれているもの。
4. SoT / generated built_in
   - pure Python で表現でき、全 target で共有価値があるもの。
5. dedicated runtime lane
   - runtime helper 自体は必要だが `core/py_runtime.h` に置くべきではないもの。

「header から別 header へ移しただけ」は、本計画では完了とみなさない。

## 現時点の分類

### A. 即削除候補

- dead include 群
  - `<cctype>`
  - `<filesystem>`
  - `<fstream>`
  - `<functional>`
  - `<regex>`
  - `<typeinfo>`
- `urllib` compile-compat shim
- `py_bool_to_string`

理由:
- 現行 `py_runtime.h` 本体か checked-in callsiteで必要性が説明できない、または emitter inline で十分だから。

### B. 上流修正後に削除する候補

- bare `len(const T&)` alias
- generic `getattr(const object&, const str&, default)`

理由:
- `len` alias は selfhost / fallback 互換の残骸であり、lowering と emitter が常に `py_len` / `RuntimeSpecialOp(len)` を使えば不要。
- `getattr` は generic helper に見えるが、現状は `type_id` probe 用途がほぼ全てであり、専用 primitive へ縮退できる。

### C. upstream binding の誤配置として扱う候補

- `print`
- `ord`
- `chr`
- `int(x, base)`

理由:
- parser/EAST が早い段階で `pytra.core.py_runtime` に束縛しており、C++ だけでなく他言語 runtime にも helper 実装を散らしている。
- これらは core object runtime の責務ではなく、builtin / scalar / io の lane で扱うべきである。

### D. 今回は主対象にしないもの

- boxing / unboxing family
- `py_at` / `py_set_at` / `py_append` / `py_extend` / `py_pop` / `py_slice`
- dynamic iteration primitive
- `py_make_scope_exit`
- process I/O primitive

理由:
- これらは C++ object model / ownership / low-level glue と強く結びついており、本件の first tranche で無理に剥がすと責務整理より回帰リスクが大きい。

## 実施方針

### S1-01 棚卸しと callsite 固定

- `py_runtime.h` 内 helper を family ごとに棚卸しし、`delete / inline / upstream / SoT / dedicated lane / keep` のどれに送るか固定する。
- 現在の checked-in callsite を、`src/`, `test/`, `sample/`, generated runtime, selfhost runtime で確認する。
- 「runtime に残っているが caller がもういない」ものと、「caller はあるが caller 側が悪い」ものを分ける。

### S1-02 置き場所の契約固定

- `py_bool_to_string` は emitter inline か `py_to_string(bool)` specialization へ寄せる方針を固定する。
- `len` alias は raw `len(...)` fallback 禁止により退役する方針を固定する。
- `getattr` は type_id 専用 probe へ縮退し、generic helper を増やさない方針を固定する。
- `print` / `ord` / `chr` / `int(x, base)` は `pytra.core.py_runtime` 固定束縛をやめ、builtin dedicated lane へ移す方針を固定する。

### S2-01 即削除 tranche

- dead include 群を削除する。
- `urllib` compat shim を削除する。
- `py_bool_to_string` を削除し、C++ emitter を inline へ置換する。

### S2-02 compat alias / generic helper 縮退 tranche

- `len` bare alias を使わない lowering / emitter / selfhost contract へ寄せる。
- `getattr` を type_id 専用 primitive へ置き換え、generic helper を撤去する。
- ここで新しい generic core helper を足して延命しない。

### S3-01 upstream binding realign tranche

- parser/EAST の builtin lowering から `print` / `ord` / `chr` / `int(x, base)` の `pytra.core.py_runtime` 固定束縛を外す。
- 必要なら `pytra.built_in.*` 側に受け皿を用意し、C++ では generated lane を使う。
- backend 側は module 名依存の ad-hoc 再解決をせず、解決済み binding を描画するだけに寄せる。

### S3-02 dedicated lane 整備

- `print` のように runtime helper 自体は必要なものは、core から外して dedicated lane に置く。
- scalar builtin (`ord` / `chr` / base-int) は SoT / generated 化できるかを判断し、可能なら pure Python SoT へ戻す。
- pure Python SoT に戻さない場合でも、`core/py_runtime.h` へ残すのではなく、責務名のある lane に隔離する。

### S4-01 回帰確認

- representative C++ runtime / bridge / backend test を通す。
- fixture parity を通し、runtime build graph が壊れていないことを確認する。
- `py_runtime.h` inventory テストや symbol index が旧 helper 在庫を前提にしていたら更新する。

### S4-02 docs / archive 同期

- spec / plan / archive / TODO の記述を current contract に同期する。
- dead helper や compat alias の削除理由を決定ログへ残す。

## 分解

- [x] [ID: P0-CPP-PYRUNTIME-UPSTREAM-REALIGN-01] `py_runtime.h` の非core helper を削除し、上流 / SoT / 専用laneへ再配置する。
- [x] [ID: P0-CPP-PYRUNTIME-UPSTREAM-REALIGN-01-S1-01] `py_runtime.h` helper family と checked-in callsite を棚卸しし、`delete / inline / upstream / SoT / dedicated lane / keep` へ分類する。
- [x] [ID: P0-CPP-PYRUNTIME-UPSTREAM-REALIGN-01-S1-02] `py_bool_to_string` / `len` alias / generic `getattr` / builtin binding の置き場所契約を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-UPSTREAM-REALIGN-01-S2-01] dead include / `urllib` compat shim / `py_bool_to_string` を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-UPSTREAM-REALIGN-01-S2-02] `len` bare alias と generic `getattr` を縮退または退役させる。
- [x] [ID: P0-CPP-PYRUNTIME-UPSTREAM-REALIGN-01-S3-01] `print` / `ord` / `chr` / `int(x, base)` の parser/EAST binding を `pytra.core.py_runtime` から外す。
- [x] [ID: P0-CPP-PYRUNTIME-UPSTREAM-REALIGN-01-S3-02] 必要な SoT / generated / dedicated runtime lane を整備し、backend を新 contract に追従させる。
- [x] [ID: P0-CPP-PYRUNTIME-UPSTREAM-REALIGN-01-S4-01] representative runtime / backend / parity test を通す。
- [x] [ID: P0-CPP-PYRUNTIME-UPSTREAM-REALIGN-01-S4-02] docs / guard / archive を同期して本件を閉じる。

## 決定ログ

- 2026-03-09: 本件は「`py_runtime.h` を物理分割して見かけの行数を減らす」計画ではなく、「core に残す理由が弱い helper を delete / inline / upstream / SoT / dedicated lane に再配置する」計画として扱う。
- 2026-03-09: 直近の `dead include + urllib` 単体計画は、本計画の `S2-01` に包含する。狭い tranche を個別 P0 として並立させず、umbrella P0 に統合する。
- 2026-03-09: checked-in callsite 棚卸しでは、`py_bool_to_string` の実使用は `src/backends/cpp/emitter/expr.py` の `render_to_string(bool)` 1 件だけだった。`urllib` compat shim は `py_runtime.h` 内にのみ存在し、checked-in caller は無い。bare `len(const T&)` alias は `py_runtime.h` 以外の native/generated C++ caller を持たず、互換残骸として扱う。generic `getattr(const object&, const str&, default)` の checked-in current use は `src/runtime/cpp/generated/built_in/type_id.cpp` の `PYTRA_TYPE_ID` probe 1 件に限られていた。
- 2026-03-09: `py_bool_to_string` は runtime core helper ではなく C++ emitter inline へ移す。bool の文字列化規約は Python 互換の `"True" / "False"` を維持し、`py_to_string(bool)` の `1/0` とは混ぜない。
- 2026-03-09: bare `len(const T&)` alias は raw fallback を許す compat とみなし、canonical lowering は `py_len(...)` / `RuntimeSpecialOp(len)` のままに固定する。`len(...)` を core helper surface として維持しない。
- 2026-03-09: generic `getattr(const object&, const str&, default)` は `PYTRA_TYPE_ID` probe を支える最小 surface として暫定維持し、generic object helper として拡張しない。char* sugar は既に削除済みで、`S2-02` では dedicated primitive 化または type_id lane への縮退を検討する。
- 2026-03-09: parser/EAST の builtin binding は現状 `print`, `len`, `range`, `zip`, `str`, `int/float/bool`, `min/max` を `pytra.core.py_runtime` へ束縛している。この tranche では特に `print`, `ord`, `chr`, `int(x, base)` を core から外すのを主目標にし、`len` は upstream canonical call として別枠で扱う。
- 2026-03-09: `S2-01` として `py_runtime.h` 先頭の dead include 6 本（`<cctype> <filesystem> <fstream> <functional> <regex> <typeinfo>`）、`urllib` compile-compat shim、`py_bool_to_string` を削除した。bool の文字列化は `CppExpressionEmitter.render_to_string()` で ternary inline に置換し、inventory guard は `test_cpp_runtime_iterable.py` に追加した。
- 2026-03-09: `S2-02` として `py_runtime.h` から bare `len(const T&)` alias と generic `getattr(const object&, const str&, default)` を削除した。`PYTRA_TYPE_ID` probe は `east2_to_east3_lowering.py` で `getattr(any_like, "PYTRA_TYPE_ID", None)` を `ObjTypeId` boundary へ縮退し、checked-in `type_id.cpp` も `py_runtime_type_id(value)` を直接使う形に更新した。
- 2026-03-09: `S3-01/S3-02` として parser/EAST binding の `print`, `ord`, `chr`, `int(x, base)` を `pytra.core.py_runtime` から切り離し、`pytra.built_in.io_ops` / `pytra.built_in.scalar_ops` へ移した。C++ runtime では dedicated lane として `src/runtime/cpp/native/built_in/io_ops.h`, `src/runtime/cpp/native/built_in/scalar_ops.h` を新設し、generated/shim header も同期した。
- 2026-03-09: C++ include 収集は `body` だけでなく `main_guard_body` も走査するように修正した。これにより top-level `print(...)` の `runtime_module_id=pytra.built_in.io_ops` が `json_extended` の main guard でも `pytra/built_in/io_ops.h` へ反映される。
- 2026-03-09: `S4-01` の確認は `test_py2cpp_features.py -k json`, `test_runtime_symbol_index.py`, `test_cpp_runtime_symbol_index_integration.py`, `test_cpp_runtime_boxing.py`, `tools/gen/gen_runtime_symbol_index.py --check`, fixture parity `cases=3 pass=3 fail=0` を通した。`test_east_core.py` 全体には unrelated failure があるため、runtime binding の subset と representative C++ backend suiteで確認した。
