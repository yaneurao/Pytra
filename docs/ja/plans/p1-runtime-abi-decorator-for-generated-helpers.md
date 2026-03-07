# P1: generated/runtime helper 向け `@abi` decorator 導入

最終更新: 2026-03-07

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RUNTIME-ABI-DECORATOR-01`

背景:
- 現状の fixed ABI 仕様は `@extern` 関数を主対象としており、external implementation を呼ぶ境界で `rc<>` を露出させないルールを定義している。
- しかし `py_runtime` 縮小や SoT 由来 runtime helper の generated 化を進めると、external ではない helper にも「内部 ref-first 表現ではなく value ABI 正規形で受けたい」ケースが出る。代表例は `str.join` 相当の helper で、`list[str]` を `rc<list<str>>` にせず `list<str>` 正規形で扱いたい。
- `@extern` に `no_body` や helper ABI を持たせて置き換える案も考えられるが、`@extern` は implementation policy、helper ABI は boundary policy であり、概念が直交している。1 decorator に混ぜると意味が濁る。
- したがって、`@extern` は残したまま、generated/runtime helper の境界 ABI だけを指定できる別 decorator が必要である。

目的:
- `@abi` decorator を導入し、generated/runtime helper の引数・戻り値ごとに fixed ABI 正規形を指定できるようにする。
- `@extern` と `@abi` の責務を分離し、external implementation と generated helper の両方で一貫した ABI ルールを適用できるようにする。
- C++ backend では `value_readonly` / `value` の最小スコープから導入し、`py_join` のような helper を pure Python SoT へ戻せる前提を作る。
- 後続の `P1-CPP-PY-RUNTIME-SLIM-01` を安全に進められるようにする。

対象:
- `docs/ja/spec/spec-abi.md`
- `src/pytra/std/__init__.py` の decorator 定義
- parser / EAST metadata / selfhost parser
- linked-program 以降の lower / ABI adapter 導線
- C++ backend の helper ABI lowering
- representative runtime helper test / C++ backend test

非対象:
- `@extern` の廃止
- helper ABI mode の全面一般化（初期は最小 mode のみ）
- user program 全般への `@abi` 一般公開
- JS/RS/CS など全 backend への同時展開
- `value_mutating` / `internal_ref` / receiver ABI の初回導入

受け入れ基準:
- `@abi` は `@extern` と独立の decorator として定義される。
- `@abi` は per-parameter / return 形式で metadata を保持できる。
- 初期 mode として少なくとも `default`, `value`, `value_readonly` を扱える。
- C++ backend は `@abi(args={"parts": "value_readonly"}, ret="value")` を理解し、`py_join` 相当 helper を `list<str>` 正規形で扱える。
- `@abi(value_readonly)` の read-only 契約に反する関数本体は compile error になる。
- `@abi` 未対応 backend / lowerer は fail-open ではなく fail-closed でエラーにするか、明示的に ignore 対象外として弾く。
- `@extern` の既存挙動は非退行で維持される。

依存関係:
- `P0-LINKED-PROGRAM-OPT-01` 完了後に着手する。
- `P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01` と競合しないが、helper ABI 選定ロジックは backend knowledge leak 撤去の data-driven 契約と整合させる。
- `P1-CPP-PY-RUNTIME-SLIM-01` は本計画の後段とする。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_*abi*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_codegen_issues.py'`
- `python3 -m py_compile src/pytra/std/__init__.py`

## 1. 問題の本質

問題は、現行の固定 ABI 仕様が「external implementation 境界」に偏っていることにある。

現状の `@extern` は次だけを表す。

- 実装本体は generated しない
- external symbol へ lower する
- 境界 ABI は固定する

しかし generated/runtime helper で本当に欲しいのは、次である。

- 実装本体は generated したい
- ただし境界 ABI は固定したい

この 2 つは別概念なので、`@extern(no_body)` のような拡張ではなく、boundary policy を別注釈へ切り出す必要がある。

## 2. 提案仕様

### 2.1 decorator 名

- user-facing decorator 名は `@abi`
- docs / 実装内部 / IR メタデータ名は `runtime_abi` としてよい

理由:

- `@abi` は短く、`@extern` と併記しても読みやすい
- 内部名では「runtime helper ABI」であることを明確にできる

### 2.2 基本記法

```python
from pytra.std import abi

@abi(args={"parts": "value_readonly"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    ...
```

初期は次の制約で導入する。

- keyword-only
- `args={name: mode}`
- `ret=mode`
- top-level function のみ

### 2.3 初期 mode

- `default`
  - override なし
- `value`
  - value ABI 正規形へ固定
- `value_readonly`
  - value ABI 正規形へ固定
  - callee は破壊的変更禁止

将来候補:

- `value_mutating`
- `internal_ref`
- `receiver`

これらは本計画では扱わない。

### 2.4 `@extern` との関係

- `@extern` は implementation policy
- `@abi` は boundary policy

両者は独立であり、併用可とする。

```python
@extern
@abi(args={"image": "value_readonly"}, ret="value")
def some_native_helper(image: list[bytearray]) -> bytes:
    ...
```

## 3. C++ での最低限の意味

`value_readonly` は、C++ では単に「コピーして `list<T>` を作る」とは限らない。

必要な契約は次である。

- ABI 正規形は `list<T>` / `dict<K,V>` / `set<T>` / `bytearray`
- 関数宣言形は `const T&` でよい
- internal `rc<>` handle から read-only borrow できるなら、その path を優先する
- 不能な場合だけ adapter/copy を挿入する

代表例:

```python
@abi(args={"parts": "value_readonly"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    ...
```

ここで `parts` を naive に internal `rc<list<str>>` としてしまうと、SoT 共有の意味が崩れる。  
`@abi` により helper signature を `list<str>` 正規形へ固定し、C++ callsite 側だけが read-only adapter を負担する形にする。

## 4. IR / metadata 方針

初期導入では、少なくとも以下を保持できるようにする。

- function decorator metadata
- parameter ごとの abi mode
- return abi mode

例:

```json
{
  "decorators": ["abi"],
  "meta": {
    "runtime_abi_v1": {
      "args": {"parts": "value_readonly"},
      "ret": "value"
    }
  }
}
```

linked-program 段では、この metadata を消さずに backend lower へ渡す。

## 5. 検証ルール

- `value_readonly` 指定パラメータに対する mutation は compile error
- unsupported backend で `@abi` 関数を transpile する場合は fail-closed
- `@extern` 既存ケースは期待値非退行
- C++ では `py_join` 相当の helper で `rc<list<str>>` を helper signature へ露出しない

## 6. フェーズ

### Phase 1: 仕様と metadata

- `spec-abi` に `@abi` を追加する
- syntax / semantics / mode / 非対象を固定する
- parser/EAST metadata の保持形式を決める

### Phase 2: parser / IR 導線

- `src/pytra/std/__init__.py` に `abi` decorator を追加する
- parser / selfhost parser が `@abi` を認識できるようにする
- EAST metadata を保持する

### Phase 3: C++ backend 最小導入

- C++ lower / adapter で `value_readonly` / `value` を解釈する
- helper signature の C++ declaration shape を固定する
- `py_join` など代表 helper を migrated path に乗せる

### Phase 4: 回帰固定

- compile error / allowed case / `@extern` 併用 case を unit test で固定する
- `py_runtime` 縮小計画の blocker を外す

## 7. タスク分解

- [x] [ID: P1-RUNTIME-ABI-DECORATOR-01-S1-01] `spec-abi` に `@abi` の syntax / semantics / mode / `@extern` との責務分離を明記する。
- [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S1-02] `@abi` metadata の EAST / linked metadata 形式を決め、parser/selfhost parser の受け入れ基準を固定する。
- [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S2-01] `src/pytra/std/__init__.py` に `abi` を追加し、parser / selfhost parser / AST build が decorator を保持できるようにする。
- [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S2-02] `value_readonly` への mutation を検出する validator / lower guard を追加する。
- [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S3-01] C++ backend に `@abi(args, ret)` の最小 lowering を実装し、helper signature を value ABI 正規形へ固定する。
- [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S3-02] `py_join` など代表 helper を `@abi` 前提に移し、`rc<list<str>>` 非露出を回帰で固定する。
- [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S4-01] `@extern` 併用 case / unsupported backend / invalid mutation case の unit test を追加する。
- [ ] [ID: P1-RUNTIME-ABI-DECORATOR-01-S4-02] docs 同期と `P1-CPP-PY-RUNTIME-SLIM-01` 依存解消メモを記録して本計画を閉じる。

## 決定ログ

- 2026-03-07: decorator 名は `@runtime_abi` ではなく user-facing に短い `@abi` を採用する方針とした。内部名・spec 用語として `runtime_abi` を使うことは許容する。
- 2026-03-07: `@abi` は `@extern` の置換ではなく、generated/helper 境界 ABI を指定する直交機能とした。
- 2026-03-07: 初期 mode は `default`, `value`, `value_readonly` に絞り、`value_mutating` などは後続拡張へ送る。
- 2026-03-08: [ID: P1-RUNTIME-ABI-DECORATOR-01-S1-01] `spec-abi` を正式仕様として締め、`@abi` の keyword-only surface、初期 mode、`@extern` との責務分離、initial acceptance rule（top-level function / runtime helper 限定、未知 mode や未知引数名は compile error）を明文化した。parser/EAST metadata の shape は `S1-02` で別固定とする。
