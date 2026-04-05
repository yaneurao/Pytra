# P0-CPP-RUNTIME-SYMBOL: C++ emitter のメソッド名ハードコードを解消する

最終更新: 2026-04-05

## 背景

C++ emitter の `emitter.py` と `header_gen.py` に Python メソッド名（`"append"`, `"clear"`, `"discard"` 等）をリストで持って mutable/immutable 判定をしている箇所がある（lint `runtime_symbol` 違反 5 件）。

```python
# emitter.py:4332-4333 (現状)
"append", "appendleft", "pop", "popleft", "clear",
"remove", "discard", "add", "update", "extend",
```

emitter が `runtime_call == "list.append"` のような文字列で判定するのも同じ emitter guide 違反。emitter は EAST3 のメタデータだけを見て写像すべき。

## 正本

`src/pytra/built_in/containers.py` にコンテナのメソッドシグネチャが `@extern class` + `mut[T]` 注釈で定義済み:

```python
@extern
class list:
    @template
    def append(self: mut[list[T]], value: T) -> None: ...
    
    @template
    def index(self: list[T], value: T) -> int: ...  # readonly
```

`mut[T]` が付いた self → mutable 操作。付いていない self → readonly 操作。

## 方針

1. spec-east.md に `Call.meta.mutates_receiver` スキーマを定義
2. resolve が `containers.py` の `@extern class` 定義を読む
3. メソッド呼び出しの解決時に `self` の型注釈が `mut[...]` なら `meta.mutates_receiver: true` を付与
4. C++ emitter は `meta.mutates_receiver` を見るだけ。メソッド名リストを削除
5. 他言語の emitter も同じフラグを使える（C++ 以外にも恩恵）

## EAST3 スキーマ

```json
{
  "kind": "Call",
  "meta": {
    "mutates_receiver": true
  }
}
```

- `mutates_receiver: true` — receiver（self）を変更する呼び出し
- フラグなし or `false` — readonly（デフォルト）
- resolve が `containers.py` の `mut[T]` 注釈から導出
- emitter はフラグのみ参照。メソッド名・runtime_call 文字列での判定は禁止

## `mut[T]` の仕様

- Python 構文として合法（型注釈は文字列として保持される）
- `from pytra.built_in import mut` — 注釈専用 no-op import（`typing` と同じ扱い）
- `self: mut[list[T]]` — self が mutable に借用される
- `dst: mut[bytearray]` — self 以外の引数にも使える
- EAST3 の `borrow_kind: "mutable_ref"` と対応
- resolve は `mut[X]` を見て `borrow_kind: "mutable_ref"` を付与し、self なら `meta.mutates_receiver: true` も付与

## 対象ファイル

- `docs/ja/spec/spec-east.md` — `Call.meta.mutates_receiver` スキーマ追加
- `src/pytra/built_in/containers.py` — 作成済み
- `src/toolchain/resolve/py/resolver.py` — `containers.py` の `mut[T]` 読み取り
- `src/toolchain/emit/cpp/emitter.py` — mutable メソッド名リスト削除、フラグベースに
- `src/toolchain/emit/cpp/header_gen.py` — 同上

## 受け入れ基準

- [ ] `Call.meta.mutates_receiver` が spec-east.md に定義されている
- [ ] resolve が `containers.py` の `mut[T]` 注釈を読んで `mutates_receiver` を導出する
- [ ] C++ emitter がメソッド名リストを持たず、フラグだけで mutable 判定する
- [ ] `check_emitter_hardcode_lint.py --lang cpp --category runtime_symbol` が 0 件
- [ ] fixture + sample parity に回帰がない

## サブタスク

1. [ ] [ID: P0-CPP-RTSYM-S1] spec-east.md に `Call.meta.mutates_receiver` を定義する
2. [ ] [ID: P0-CPP-RTSYM-S2] resolve が `src/pytra/built_in/containers.py` を読み、`mut[T]` 注釈付きメソッドの Call に `meta.mutates_receiver: true` を付与する
3. [ ] [ID: P0-CPP-RTSYM-S3] C++ emitter の mutable メソッド名リストを `meta.mutates_receiver` ベース��判定に置き換える
4. [ ] [ID: P0-CPP-RTSYM-S4] `check_emitter_hardcode_lint.py --lang cpp --category runtime_symbol` が 0 件になることを確認する

## 決定ログ

- 2026-04-05: `containers.py` を `@extern class` + `mut[T]` 注釈で作成済み。resolve 統合と emitter 移行を計画。emitter guide 違反（メソッド名ハードコード）の根本解決。
