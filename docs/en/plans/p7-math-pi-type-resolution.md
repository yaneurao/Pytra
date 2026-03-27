<a href="../../ja/plans/p7-math-pi-type-resolution.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p7-math-pi-type-resolution.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p7-math-pi-type-resolution.md`

# P7: linker post-link pass でモジュール属性の型を解決

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P7-MODULE-CONST-TYPE`

## 背景

`2.0 * math.pi * t` のような式で `math.pi` の `resolved_type` が `unknown` になり、emitter が型不一致を起こす。

EAST1 パーサーは `math.pi` の owner type を `unknown` と推論する（`math` は import モジュール名であり `name_types` に型登録されない）。EAST1 パーサーに個別モジュールの型情報をハードコードすると `noncpp_runtime_call` と同じ問題（EAST1 の責務逸脱）を繰り返す。

モジュール属性の型情報は各モジュールの EAST3（`.east` ファイル）に含まれており、linker がモジュールを解決した後に参照可能。

## 設計

linker の post-link pass で汎用的にモジュール属性の型を解決する:

### Step 1: export テーブル収集

linked program の全モジュールの EAST3 body を走査し、トップレベルの変数・定数の型を収集:

```python
# module_id="pytra.std.math" の body から:
#   pi: float = 3.14159...  → exports["pi"] = "float64"
#   e: float = 2.71828...   → exports["e"] = "float64"

module_exports: dict[str, dict[str, str]] = {
    "pytra.std.math": {"pi": "float64", "e": "float64", ...},
    "pytra.std.os": {"sep": "str", ...},
    ...
}
```

対象ノード:
- `AnnAssign`（`pi: float = ...`）→ `annotation` / `decl_type` から型取得
- `Assign`（`sep = "/"` ）→ `decl_type` / value の `resolved_type` から型取得
- `FunctionDef`（`def sqrt(x: float) -> float`）→ `return_type` から戻り値型取得（関数属性アクセス用）

### Step 2: Attribute ノードの resolved_type 更新

linked program の全モジュールを再走査し、Attribute ノードで:
1. owner が import モジュール名（`import_module_bindings` で解決可能）
2. `resolved_type` が `unknown` または空

の場合、export テーブルから型を埋める。

### Step 3: BinOp 等の結果型の再計算（optional）

Attribute の型が更新されると、`2.0 * math.pi` の BinOp の結果型も `float64` に確定できる。これは既存の integer promotion パスと同様のロジックで対応可能。

## 対象

| ファイル | 変更内容 |
|---|---|
| `src/toolchain/link/` 配下（新規または既存） | post-link pass: export テーブル収集 + Attribute 型解決 |

## 非対象

- EAST1 パーサーへのハードコード（禁止）
- `signature_registry.py` へのモジュール固有情報追加（禁止）
- emitter 側での個別対応

## 受け入れ基準

- [ ] `math.pi` の `resolved_type` が linked program 内で `float64` に解決される
- [ ] `os.sep` 等の他モジュール属性も同様に解決される
- [ ] ユーザー定義モジュールの属性も解決される
- [ ] EAST1 パーサー / signature_registry にハードコードが追加されない
- [ ] 既存テストがリグレッションしない

## 子タスク

- [ ] [ID: P7-MODULE-CONST-TYPE-01] linked program の全モジュールからトップレベル export テーブルを収集する
- [ ] [ID: P7-MODULE-CONST-TYPE-02] Attribute ノードの `resolved_type` を export テーブルで更新する post-link pass を実装する
- [ ] [ID: P7-MODULE-CONST-TYPE-03] ユニットテストを追加する

## 決定ログ

- 2026-03-22: Zig 担当が `2.0 * math.pi * t` で `resolved_type=unknown` になる問題を報告。全 backend 共通の改善として起票。
- 2026-03-22: EAST1 パーサーへのハードコード案（`signature_registry` に `math.pi` 等を追加）を検討したが、EAST1 の責務逸脱と判断し却下。linker の post-link pass でモジュール EAST3 の body からトップレベル export を収集し、汎用的に Attribute 型を解決する方針に決定。
