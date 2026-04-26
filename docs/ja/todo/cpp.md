<a href="../../en/todo/cpp.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — C++ backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-26

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## selfhost 作業の運用ルール（C++ を先行させる方針）

1. **C++ を 1 言語先行させる**。他言語の selfhost は C++ で判断基準が固まってから着手する。
2. **backend 側で対処できる問題は自律的に修正してよい**。具体的には:
   - C++ emitter の generator ロジックの修正
   - C++ runtime（`src/runtime/cpp/`）の補完
   - C++ mapping.json の追加・修正
   - 既存の EAST3 metadata を見落としていた場合のハンドリング追加
3. **「EAST 側の修正が必要かも」と思ったら作業を停止して報告する**。該当するのは:
   - EAST3 に必要な情報がそもそも無い（metadata 欠落、kind 不足）
   - resolver / compiler / optimizer が情報を正しく付けていない
   - 修正が他言語（Rust, TS, Go, Java 等）にも影響する可能性がある
   - どちらで直すべきか判断に迷う
4. **判断は 1 件ずつ人間（PM）が行う**。バッチ報告ではなく、発生した時点で即停止・即報告・即判断。

### 問題報告フォーマット

```
## 問題: <短い要約>

**症状**: selfhost emit → build で何が失敗するか（エラーメッセージの原文）
**場所**:
  - source（selfhost 対象の Python）: src/toolchain/... : line
  - emit 結果の該当 C++: <抜粋>
  - 該当 EAST3 ノード: <kind, 主要 field の抜粋>
**backend 側で対処する案**: どう修正するか、副作用
**EAST 側で対処する案**: どう修正するか、他言語への影響
**担当の見立て**: どちらが妥当か（理由）
```

## 未完了タスク

### P1-EMITTER-SELFHOST-CPP: emit/cpp/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.cpp.cli` をエントリに単独で C++ build を通す。

1. [x] [ID: P1-EMITTER-SELFHOST-CPP-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target cpp -o work/selfhost/emit/cpp/` を実行し、変換が通るようにする
   - 2026-04-25: `types.py` の top-level dict/set literal と標準 `re` 依存を selfhost-safe な builder/scanner に置換。`python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target cpp -o work/selfhost/emit/cpp/` が parse/resolve/compile/optimize/link と C++ emit まで通過。
2. [x] [ID: P1-EMITTER-SELFHOST-CPP-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
	   - 2026-04-25: `cli_runner.py` / `cpp/cli.py` / `code_emitter.py` の `JsonVal` に対する `isinstance` と optional 判定の一部を `JsonValue` accessor と段階的な `None` check に置換。`g++ -std=c++20 -O0 -fmax-errors=60` の次 blocker は `common_renderer` 生成ヘッダの重複宣言、class field 未生成、残りの `isinstance` lowering。
	   - 2026-04-25: `common_renderer.py` の重複メソッド定義を整理し、C++ struct に必要な field annotation を追加。生成ヘッダの重複宣言と member 未生成は解消。次 blocker は `common_renderer` の profile helper 群に残る `JsonVal` `isinstance` lowering。
	   - 2026-04-25: `common_renderer.py` の profile/with/exception/expr helper を `JsonValue` accessor と段階的な EAST node 構築へ寄せ、`cpp/cli.py` の selfhost entry 名衝突と `cli_runner.py` の positional 呼び出し互換性を修正。`header_gen.py` は `Callable[...]` で `<functional>` を出すよう補完。`g++` の次 blocker は `cpp/emitter.py` 先頭側に残る `isinstance` lowering と、`str`/`int64` 返却値への不要な `.unbox<T>()` 生成。
	   - 2026-04-26: `types.py` の長大な `or` chain 生成を set membership に変更し、C++ helper の private symbol 衝突、header/definition の mutable/const 不一致、`std/subprocess.h` 欠落を修正。`python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target cpp -o work/selfhost/emit/cpp/` と、runtime 込みの `g++ -std=c++20 -O0 ... -o work/selfhost/emit/cpp/build/cpp_emitter_selfhost` が終了コード 0。残りは `_emit_expr_extension` などの non-void warning。
3. [x] [ID: P1-EMITTER-SELFHOST-CPP-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する
   - 2026-04-26: `test/fixture/source/py/core/assign.py` の linked manifest をコンパイル済み `work/selfhost/emit/cpp/build/cpp_emitter_selfhost` に渡し、Python 版 emitter 出力との `diff -ru` が終了コード 0。途中で見つかった `CppEmitContext` / `CommonRendererState` の default_factory 未初期化、共通 renderer の非 virtual dispatch 依存、`JsonVal is not None` 判定、`self_header` keyword lowering 依存を修正。


### P0-RESOLVE-ISINSTANCE-NARROWING: union 型に対する isinstance narrowing を修正する

文脈: [docs/ja/plans/p0-resolve-isinstance-narrowing.md](../plans/p0-resolve-isinstance-narrowing.md)

**発端**: C++ selfhost build で `isinstance(value, dict)` 後の narrowing が bare `dict`（パラメータなし）になり、emitter が `dict` と `dict[str, JsonVal]` を別の型と誤判定して covariant copy ラムダを生成 → g++ で `push_back` 未定義エラー。

**問題**: `value` の型が `JsonVal`（= `None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]`）のとき、`isinstance(value, dict)` で narrowing すると `dict`（bare）になる。union の構成要素に `dict[str, JsonVal]` しかないのだから、narrowing 結果は `dict[str, JsonVal]` であるべき。

**方針**: resolve の isinstance narrowing が、union 型の構成要素からマッチする型をパラメータ付きで取り出すようにする。

1. [x] [ID: P0-RESOLVE-NARROW-S1] resolve の isinstance narrowing で、union 型の構成要素から `isinstance` の判定対象にマッチする型をパラメータ付きで取り出すよう修正する
2. [x] [ID: P0-RESOLVE-NARROW-S2] `isinstance(value, dict)` で `dict[str, JsonVal]` に narrowing されることを確認するテストを追加する
3. [x] [ID: P0-RESOLVE-NARROW-S4] elif/else チェーンでの段階的 union narrowing を実装する。isinstance の偽ブランチで、マッチした型を union から除外し、残りの構成要素を resolved_type にする。残りが 1 つなら単一型に narrowing する
4. [x] [ID: P0-RESOLVE-NARROW-S5] `isinstance_chain_narrowing` fixture で C++ が PASS することを確認する

### P0-RESOLVE-TYPE-ALIAS: 型エイリアスの同値性判定を正しく実装する

文脈: [docs/ja/plans/p0-resolve-type-alias.md](../plans/p0-resolve-type-alias.md)

**発端**: `Node = dict[str, JsonVal]` のとき、`list[Node]` に `dict[str, JsonVal]` を append すると emitter が型不一致と判定する。

**問題**: `normalize_type` が型エイリアス展開と構文正規化を混在させており、再帰型（`JsonVal`）を展開すると `Any` に退化する。結果として型エイリアスの同値性が保証されない。

**方針**:
- 非再帰型エイリアスは完全展開する
- 自己再帰型エイリアスは名前を保持する（展開しない）
- 相互再帰型エイリアスは禁止する（parse 時にエラー）
- これにより、展開後の型表現が一意に定まり、`Node` と `dict[str, JsonVal]` の同値性が保証される

1. [x] [ID: P0-RESOLVE-ALIAS-S1] `normalize_type` の再帰型ガードを `Any` 退化から名前保持に変更する
2. [x] [ID: P0-RESOLVE-ALIAS-S2] 相互再帰型エイリアスを parse 時にエラーにする
3. [x] [ID: P0-RESOLVE-ALIAS-S3] `Node` → `dict[str, JsonVal]` 展開、`JsonVal` → 名前保持のテストを追加する
4. [x] [ID: P0-RESOLVE-ALIAS-S5] spec に「型エイリアスの相互再帰は禁止。自己再帰は名前保持」を明記する

### P0-COMMON-RENDERER-UNION-MEMBER: union 構成要素の格納で covariant copy をスキップする

文脈: [docs/ja/plans/p0-common-renderer-union-member.md](../plans/p0-common-renderer-union-member.md)

**発端**: C++ selfhost で `list[JsonVal].append(stmt)` が covariant copy ラムダに誤変換。`stmt` は `dict[str, JsonVal]` で `JsonVal` の union 構成要素。variant への単純格納で済むのに dict の push_back を呼んで g++ エラー。

**方針**: CommonRenderer に `_is_union_member(member_type, union_type)` helper を追加。append / 代入時に引数型が要素型の union 構成要素なら covariant copy をスキップして単純格納にする。全言語共通。

1. [x] [ID: P0-CR-UNION-S1] CommonRenderer 相当の共通 type helper に union member 判定を実装する
2. [x] [ID: P0-CR-UNION-S2] `list[Union].append(member)` で union 構成要素の場合に covariant copy をスキップするよう修正する
3. [x] [ID: P0-CR-UNION-S3] C++ selfhost の `list[JsonVal].append(dict[str, JsonVal])` が単純格納に変換されることを確認する

### P0-RESOLVE-FIELD-TYPES: __init__ の self.<field> 代入から ClassDef.field_types を埋める

**発端**: selfhost で `alias_arg.py` 等の ClassDef.field_types が `{}` のまま C++ emitter に届き、struct ヘッダにメンバが出ずコンパイル失敗。

**問題**: parser は `__init__` body の `self.attr = value` を走査して field_types を埋めようとするが、パラメータに型注釈がない場合や名前が一致しない場合は推論できず空のまま。resolver は既存の field_types を正規化するだけで、式の resolved_type からの補完をしない。

**方針**: resolver の `_resolve_class` で `__init__` body を resolve した後に `self.attr = expr` を再走査し、field_types に未登録のフィールドを `expr.resolved_type` から補完する。parser 段階では型が未解決なので resolver でやるのが正道。

1. [x] [ID: P0-RESOLVE-FIELD-S1] resolver の `_resolve_class` で `__init__` body の `self.attr = expr` から field_types を補完する
2. [x] [ID: P0-RESOLVE-FIELD-S2] `alias_arg` fixture が field_types 付きで EAST3 を出力し、C++ parity PASS することを確認する
3. [x] [ID: P0-RESOLVE-FIELD-S3] `__init__` 以外のメソッドで self.attr に代入するケースの扱いを決める（v1 では __init__ のみ対象）
   - 2026-04-26: v1 は `__init__` 内の `self.attr` のみ補完対象。annotation-only の class body 宣言は instance field 宣言として維持。

### P0-CLASS-VAR-VS-FIELD: class 変数と instance field の metadata を分離する

**発端**: `class_member.py` の `Counter.value: int = 0` が field_types に入り、C++ emitter が instance field としてヘッダに出力する一方、本体側では `Counter_value` グローバルとして出力して不一致。

**問題**: EAST3 の ClassDef.field_types に class 変数と instance field が混在して入り、`class_storage_hint` だけでは区別できない。

**方針**: field_types の各エントリに `"class_var"` / `"instance"` のフラグを追加するか、`class_var_types` を別フィールドとして分離する。spec-east.md §11 のクラス情報事前収集に追記が必要。

1. [x] [ID: P0-CLASSVAR-S1] ClassDef に `class_var_types` を追加し、class body の直接 `AnnAssign` を class_var、`__init__` 内の `self.attr` を instance field として分離する
2. [x] [ID: P0-CLASSVAR-S2] C++ emitter が class_var を static / グローバル変数として、instance field を struct メンバとして出力することを確認する
3. [x] [ID: P0-CLASSVAR-S3] `class_member` fixture が C++ parity PASS することを確認する
   - 2026-04-26: 非 dataclass で値を持つ class body `AnnAssign` / `Assign` を `class_var_types` に分離。C++ header の const 判定も class storage mutation を見るよう補正。

### P1-LOWER-STARRED-EXPAND: Call.args 内の Starred を lower で展開する

**発端**: `starred_call_tuple_basic.py` の `draw(*rgb)` が host C++ emit でも `unsupported_expr_kind: Starred` で落ちる。

**問題**: lower.py は Starred ノードをそのまま EAST3 に通過させるが、C++ emitter（および他言語 emitter）は Starred を処理できない。EAST3 を backend-friendly IR にする方針に沿い、静的に展開可能な Starred は lower で引数に inline 展開すべき。

**方針**: lower の Call 処理で、Starred の value が静的サイズの tuple 型のとき、tuple 要素数分の Subscript に展開する。動的サイズや不明型の場合は `unsupported_syntax` で fail-closed。

1. [x] [ID: P1-LOWER-STARRED-S1] lower.py の `_lower_call_expr` で Starred(tuple) を静的展開する
2. [x] [ID: P1-LOWER-STARRED-S2] validate_east3 に Starred 残留検出を追加する（For 残留検出と同様）
3. [x] [ID: P1-LOWER-STARRED-S3] `starred_call_tuple_basic` fixture が C++ parity PASS することを確認する
   - 2026-04-26: fixed tuple の `*arg` を `Subscript` 引数列へ展開し、EAST3 validator で `Starred` 残留を禁止。

### P20-CPP-SELFHOST: C++ emitter で toolchain を C++ に変換し g++ build を通す

文脈: [docs/ja/plans/p4-cpp-selfhost.md](../plans/p4-cpp-selfhost.md)

S0〜S4 完了済み（[archive/20260402.md](archive/20260402.md) 参照）。

1. [x] [ID: P20-CPP-SELFHOST-S5] selfhost C++ バイナリを g++ でビルドし、リンクが通ることを確認する
   - build 失敗の都度、backend で直るか EAST 修正が必要か判断する
   - EAST 修正が必要と思われる場合は **作業を停止し、問題報告フォーマットで報告する**
   - 2026-04-11: `expand_defaults.py → type_norm.py` の transitive closure 疑いは infra 側で誤診と確定。closure 自体は保持されており、現在は g++ build の残 blocker に戻っている。
   - 2026-04-13: resolve narrowing / type alias / union member append の前提 TODO を先に消化。次は fresh selfhost build を再開する。
   - 2026-04-26: `src/pytra-cli.py` 全体を C++ emit し、`g++ -O0 -std=c++20` で runtime sources 11 件込みの selfhost binary `work/selfhost/bin/cpp` を link 成功。`./work/selfhost/bin/cpp --help` も終了コード 0。途中 blocker は `TargetPlanDraft` keyword lowering、`TypeSummary` str unbox、resolver の classmethod/tuple set/dict literal narrowing、常時 TRACE 出力を selfhost-safe に修正。
2. [ ] [ID: P20-CPP-SELFHOST-S6] `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root fixture` で fixture parity が PASS することを確認する
   - 2026-04-26: selfhost binary 内 C++ emitter の entry `set_argv(...)` を `sys` 依存時だけ出すよう修正し、代表 `add.py` は selfhost emit/run まで PASS。full fixture parity は `fixture_pass=115 / fixture_fail=46`。残りは `alias_arg` / `class_member` など host C++ emit でも compile 失敗する既存 C++ backend 問題と、`starred_call_tuple_basic` の selfhost `Starred` 未対応など。
   - 2026-04-26: full fixture parity は `fixture_pass=122 / fixture_fail=39` まで改善。追加で top-level `def main()` の C++ 実 entry 衝突と `enumerate(list[T])` lowering の壊れた range 変換を修正し、`class_body_pass` / `slice_basic` / `enumerate_basic` / `reversed_enumerate` は host C++ と selfhost C++ emit/run の両方で PASS。S6 全体は未完了。
   - 2026-04-26: 修正済み selfhost binary で full fixture parity を再実行し、`fixture_pass=134 / fixture_fail=27` を確認。S6 全体は未完了。
   - 2026-04-26: C++ header generator の enum 前方宣言を `enum class <Name> : int64;` に揃え、selfhost C++ の `enum_basic` / `intenum_basic` / `intflag_basic` が emit/run まで PASS。S6 全体は未完了。
   - 2026-04-26: C++ emitter が `type.isinstance` の Call を既存 `_emit_isinstance` 経路へ通すよう修正し、selfhost C++ の `class_inherit_basic` / `is_instance` / `isinstance_user_class` が emit/run まで PASS。trait 系は別原因で未完了。
   - 2026-04-26: 空 `set[tuple[...]]` ctor の C++ 型名生成と `@property` getter 属性参照を修正し、host C++ parity と selfhost C++ emit/run の両方で `object_container_access` / `property_method_call` が PASS。S6 全体は未完了。
   - 2026-04-26: `dict[str, object].get(...)` を `str()` へ渡す動的 object 境界を `py_to_string` 経由に修正し、host C++ parity と selfhost C++ emit/run の両方で `typed_container_access` が PASS。S6 全体は未完了。
   - 2026-04-26: list RHS の unpack 一時変数 `__tuple_unpack_*` を `std::get` に誤分類しないよう修正し、host C++ parity と selfhost C++ emit/run の両方で `tuple_unpack_variants` が PASS。S6 全体は未完了。
   - 2026-04-26: `py_assert_eq` の expected 側空 `[]` を actual 側の `list[T]` lane で出すよう修正し、host C++ parity と selfhost C++ emit/run の両方で `reversed_basic` / `sorted_set` が PASS。S6 全体は未完了。
   - 2026-04-26: union の dict lane に対する `.items()` 呼び出しを C++ emitter 側で lane 取得して `py_dict_items` に写像するよう修正し、host C++ parity と selfhost C++ emit/run の両方で `union_basic` / `union_dict_items` が PASS。S6 全体は未完了。
   - 2026-04-26: `isinstance(x, (A, B))` を C++ emitter で単一型判定の OR に展開し、with lowering の context/as 変数を C++ で参照束縛できる形に修正。host C++ parity と selfhost C++ emit/run の両方で `isinstance_tuple_check` / `with_context_manager` が PASS。S6 全体は未完了。
   - 2026-04-26: narrowing 後の union Name / subscript / for iterable で C++ variant lane を取り出すよう修正し、`is None`/`isinstance` 判定は storage 全体を見るよう補正。host C++ parity と selfhost C++ emit/run の両方で `isinstance_chain_narrowing` / `isinstance_union_narrowing` が PASS。S6 全体は未完了。
   - 2026-04-27: C++ emitter で `Path / rhs` を `Path::joinpath(rhs)` に直接変換し、try-finally lowering 後の `AnnAssign` を try 外へ事前宣言するよう修正。host C++ parity と selfhost C++ emit/run の両方で `with_statement` が PASS。S6 全体は未完了。
   - 2026-04-27: C++ emitter で typed varargs を `list[T]` パラメータとして受け、呼び出し側の余剰引数を `list[T]{...}` に pack するよう修正。host C++ parity と selfhost C++ emit/run の両方で `ok_typed_varargs_representative` が PASS。S6 全体は未完了。
3. [ ] [ID: P20-CPP-SELFHOST-S7] `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root sample` で sample parity が PASS することを確認する
