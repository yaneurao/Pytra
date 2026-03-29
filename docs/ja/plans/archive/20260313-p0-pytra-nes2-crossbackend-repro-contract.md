<a href="../../../en/plans/archive/20260313-p0-pytra-nes2-crossbackend-repro-contract.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: Pytra-NES2 repro を全言語 representative contract として固定する

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01`

背景:
- `materials/refs/from-Pytra-NES2/` には、別チームが `Pytra -> C++ -> g++` で遭遇した停止点を切り出した minimal repro 群が置かれている。
- 2026-03-13 時点で、この bundle を手元確認した結果、`bytes_truthiness.py`、`path_stringify.py`、`field_default_factory_rc_obj.py` は現行 repo では再現せず、既存 fixture / smoke / archive task に取り込まれている。
- 一方で、`property_method_call.py` は `@property` 参照が C++ 側でメソッドポインタ相当の式に落ちる compile error を再現し、`list_bool_index.py` は `list[bool]` の read/write が `std::vector<bool>` proxy と衝突する compile error を再現した。
- しかし、この 2 件を C++ backend 局所バグとして閉じると、他 backend が同じ semantics を壊していても見逃す。ユーザー指示は「まず test を書き、その test が全言語で通ることをクリア条件にする」ことであり、backend 個別修正を先に行うことではない。
- したがって、この task は Pytra-NES2 repro を `materials/refs/` の参考資料から `test/fixtures/` と backend smoke へ昇格し、`@property` read と `list[bool]` index read/write を全 backend の representative contract として固定するために起票する。

目的:
- `property_method_call.py` と `list_bool_index.py` を全 backend 共通の representative fixture に昇格する。
- C++ だけでなく、`cpp`, `cs`, `rs`, `go`, `java`, `kotlin`, `scala`, `swift`, `nim`, `js`, `ts`, `lua`, `ruby`, `php` の smoke / contract に同じ semantics を固定する。
- 「この 2 件が全言語で通る」ことを close 条件とし、backend ごとの silent fallback や unsupported 逃がしを防ぐ。

対象:
- `materials/refs/from-Pytra-NES2/{property_method_call.py,list_bool_index.py}`
- new representative fixtures under `test/fixtures/**`
- backend smoke:
  - `tools/unittest/emit/cpp/test_py2cpp_features.py`
  - `tools/unittest/emit/cs/test_py2cs_smoke.py`
  - `tools/unittest/emit/rs/test_py2rs_smoke.py`
  - `tools/unittest/emit/go/test_py2go_smoke.py`
  - `tools/unittest/emit/java/test_py2java_smoke.py`
  - `tools/unittest/emit/kotlin/test_py2kotlin_smoke.py`
  - `tools/unittest/emit/scala/test_py2scala_smoke.py`
  - `tools/unittest/emit/swift/test_py2swift_smoke.py`
  - `tools/unittest/emit/nim/test_py2nim_smoke.py`
  - `tools/unittest/emit/js/test_py2js_smoke.py`
  - `tools/unittest/emit/ts/test_py2ts_smoke.py`
  - `tools/unittest/emit/lua/test_py2lua_smoke.py`
  - `tools/unittest/emit/rb/test_py2rb_smoke.py`
  - `tools/unittest/emit/php/test_py2php_smoke.py`
- 必要なら共通 smoke helper / fixture lookup / backend contract checker
- docs / support wording / TODO

非対象:
- `bytes_truthiness.py`, `path_stringify.py`, `field_default_factory_rc_obj.py` の再修正
  - これらは既存 representative lane として別 task 群で扱われている。
- `materials/refs/from-Pytra-NES2/path_alias_pkg/entry.py`
  - README に記載はあるが、current bundle に現物が存在しないため、この task の対象外とする。
- この turn での実装修正
- repro bundle 全体の一括 archive 化

受け入れ基準:
- `property_method_call.py` と `list_bool_index.py` が `test/fixtures/` 下の representative fixture として追加される。
- fixture の expected semantics が docs / test 名 / assertion で明文化される。
  - `property_method_call`: `@property` read が値として評価され、比較と `str(...)` で method object 扱いにならない。
  - `list_bool_index`: `list[bool]` の index read/write が両方成立し、`not` 代入後の再読込が正しい。
- 対象 backend 全部に、少なくとも 1 本ずつこの fixture を触る representative smoke / contract test が追加される。
- close 条件は「対象 backend 全部で、その representative test が green」であり、C++ 単独 green では閉じない。
- unsupported / preview_only / not_implemented などの診断へ逃がす場合は close 不可とし、task は未完了のまま残す。
- `materials/refs/from-Pytra-NES2/README.md` の repro と、repo 内 fixture/test の対応表が docs / 決定ログで追跡できる。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cs -p 'test_py2cs_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/rs -p 'test_py2rs_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/go -p 'test_py2go_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/java -p 'test_py2java_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/kotlin -p 'test_py2kotlin_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/scala -p 'test_py2scala_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/swift -p 'test_py2swift_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/nim -p 'test_py2nim_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/js -p 'test_py2js_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/ts -p 'test_py2ts_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/lua -p 'test_py2lua_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/rb -p 'test_py2rb_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/php -p 'test_py2php_smoke.py'`
- `git diff --check`

実施方針:
1. `materials/refs/` は外部報告の原本として残し、repo の正本は `test/fixtures/` と backend smoke に昇格した representative fixture とする。
2. 先に fixture と全 backend smoke を追加し、失敗を固定する。backend 実装修正はその後に行う。
3. C++ compile error を再現している cases でも、テストの意味は「C++ を直す」ではなく「全 backend が同じ semantics を満たす」ことに置く。
4. 既存の per-backend unsupported escape hatch で逃がさず、全 backend green を close 条件として TODO / plan に固定する。
5. この task は実装修正の親 task であり、必要な backend 切り分けは子 task へ分割してよいが、親 close 条件は最後まで「全 backend representative test green」を維持する。

## current repro inventory

| README entry | current bundle | current repo status | representative lane |
| --- | --- | --- | --- |
| `bytes_truthiness.py` | present | covered elsewhere | `test/fixtures/typing/bytes_truthiness.py` + C++ representative smoke |
| `path_stringify.py` | present | covered elsewhere | `test/fixtures/stdlib/path_stringify.py` + C++ representative smoke |
| `field_default_factory_rc_obj.py` | present | covered elsewhere | archived C++ representative lane (`field(default_factory=...)` on `rc<T>`) |
| `property_method_call.py` | present | promoted and green | `test/fixtures/typing/property_method_call.py` + representative smoke across all backends |
| `list_bool_index.py` | present | promoted and green | `test/fixtures/typing/list_bool_index.py` + representative smoke across all backends |
| `path_alias_pkg/entry.py` | missing | not triaged | out of scope until the bundle includes the file |

## representative semantics

### `property_method_call`

source:
- `materials/refs/from-Pytra-NES2/property_method_call.py`

固定したい意味:
- `@property` 付き member access は value read として扱う。
- `self.mapper == 4` は property getter の戻り値と `4` の比較になる。
- `str(self.mapper)` は property getter の戻り値を文字列化する。
- method symbol そのもの、callable object、bound method として lower してはならない。

### `list_bool_index`

source:
- `materials/refs/from-Pytra-NES2/list_bool_index.py`

固定したい意味:
- `current = flags[index]` の read が成立する。
- `flags[index] = not current` の write が成立する。
- write 後の `flags[index]` 再読込が最新値を返す。
- `list[bool]` だけ特殊コンテナ扱いになって read/write contract が壊れてはならない。

## 分解

- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01] Pytra-NES2 repro を全 backend representative contract に昇格し、`property_method_call` と `list_bool_index` の test が全言語で通る状態を close 条件として固定した。
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S1-01] `materials/refs/from-Pytra-NES2/` の current repro inventory を棚卸しし、既存対応済み case と未対応 case の対応表を plan / docs に固定する。
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S1-02] `property_method_call.py` と `list_bool_index.py` を `test/fixtures/` の representative fixture へ昇格し、期待 semantics を assertion 付きで固定する。
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S2-01] C++/C#/Rust/Go/Java/Kotlin/Scala/Swift/Nim の representative smoke に 2 fixture を追加し、C++ current compile-failure baseline と static family の transpile smoke を固定する。
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S2-02] JS/TS/Lua/Ruby/PHP の representative smoke に 2 fixture を追加し、script family の representative transpile contract を固定する。
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S2-03] 全 backend 共通で「unsupported / preview_only / not_implemented へ逃がしたら fail」と分かる assertion / helper / checker を必要に応じて追加する。
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S3-01] `property_method_call` の全 backend green を達成し、docs / support wording / decision log を同期する。
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S3-02] `list_bool_index` の全 backend green を達成し、docs / support wording / decision log を同期する。
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S4-01] `materials/refs/from-Pytra-NES2` と repo fixture/test の対応を最終同期し、この repro bundle を「全 backend representative contract に昇格済み」として close した。

決定ログ:
- 2026-03-13: ユーザー指示に従い、未解消 2 件を C++ 局所 bugfix task として閉じる方針をやめ、まず全 backend representative test を追加してから実装修正へ進む P0 に切り替えた。
- 2026-03-13: current repro bundle のうち `bytes_truthiness`, `path_stringify`, `field_default_factory_rc_obj` は既存 fixture / smoke に取り込まれている一方、`property_method_call` と `list_bool_index` は current repo で未解消と判定した。
- 2026-03-13: README 記載の `path_alias_pkg/entry.py` は current bundle に現物がないため、この task の対象から外し、別途 bundle 補完が来たときに再評価する。
- 2026-03-13: `S1-01` として README entry ごとの current bundle / current repo status / representative lane を table 化し、既存 3 件、未解消 2 件、missing 1 件を plan 正本に固定した。
- 2026-03-13: `S1-02` として `test/fixtures/typing/property_method_call.py` と `test/fixtures/typing/list_bool_index.py` を追加し、`@property` value read / stringify と `list[bool]` read-write-reread semantics を assertion 付きで固定した。
- 2026-03-13: `S2-01` として `property_method_call` / `list_bool_index` を `cpp` current compile-failure baseline と `cs/rs/go/java/kotlin/scala/swift/nim` representative transpile smoke へ接続した。`property_method_call` は property read が member-function pointer 扱いになって compile error、`list_bool_index` は `std::vector<bool>` proxy が `bool&` と衝突する compile error を current baseline として固定した。
- 2026-03-13: `S2-02` として `property_method_call` / `list_bool_index` を `js/ts/lua/ruby/php` representative transpile smoke へ接続し、Wave B でも unsupported / preview に逃がさず少なくとも transpile surface を通す contract を固定した。
- 2026-03-13: `S2-03` として `tools/unittest/emit/representative_contract_support.py` に共通 denylist helper を追加し、全 backend representative smoke が `unsupported / preview_only / not_implemented` marker を含むと fail するようにした。C++ current baseline は compile stderr ではなく生成 C++ source 自体に対して helper を適用し、escape marker を含まない compile-failure baseline だけを許可した。
- 2026-03-13: `S3-01` として C++ emitter に class-local `@property` getter track を追加し、attribute read を `this->mapper()` / `holder->mapper()` へ lower するように修正した。これで `property_method_call` は C++ も compile+run green になり、全 backend representative lane が green になったため、残件は `list_bool_index` のみとなった。
- 2026-03-13: `S3-02` として C++ runtime の `list<T>` / `py_at` / `py_list_at_ref` を `list<T>::reference/const_reference` ベースにし、`make_object` に bool-convertible proxy fallback を追加した。これで `std::vector<bool>` proxy と `bool&` の衝突が消え、`list_bool_index` は C++ でも compile+run green になった。
- 2026-03-13: `S4-01` として `materials/refs/from-Pytra-NES2` と repo fixture/test の最終対応を同期した。`bytes_truthiness` は `test/fixtures/typing/bytes_truthiness.py` と archived representative lane、`path_stringify` は `test/fixtures/stdlib/path_stringify.py` と archived representative lane、`field_default_factory_rc_obj` は archived dataclass representative lane、`property_method_call` / `list_bool_index` は `test/fixtures/typing/*` と全 backend representative smoke へそれぞれ昇格済みと確定した。`path_alias_pkg/entry.py` は bundle に現物がないため out-of-scope のまま close する。
