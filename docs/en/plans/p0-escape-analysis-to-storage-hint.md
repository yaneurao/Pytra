<a href="../../ja/plans/p0-escape-analysis-to-storage-hint.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-escape-analysis-to-storage-hint.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-escape-analysis-to-storage-hint.md`

# P0: escape 解析結果を class_storage_hint に反映する

最終更新: 2026-03-20

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-ESCAPE-TO-STORAGE-HINT-01`

## 背景

現在 `class_storage_hint`（value / ref）はパーサー段（`core_module_parser.py`）で静的に決定される。escape 解析（`NonEscapeInterproceduralPass`）はリンカー段で関数引数の escape 情報を `non_escape_summary` に記録するが、この結果が `class_storage_hint` に反映されない。

### 現状の問題

1. パーサーが `Path` を value 候補と判定（メソッドなし or フィールドのみのクラス）
2. `Path.__init__(self, value: str | Path)` で `Path` が union type 引数に渡される = `object` に box = escape
3. escape 解析はこれを検出するが、`class_storage_hint` を変更しない
4. emitter が value 型として emit → `RcObject` 非継承 → `object` に入れられない

### 暫定対応

`core_module_parser.py` で union type パラメータを持つクラスを `ref` に強制する判定を追加した。しかしこれはパーサーでのハードコードであり、escape 解析の結果ではない。

## 設計

### 正しいフロー

```
compile 段: class_storage_hint = "value"（パーサーの静的判定）
    ↓
link 段: NonEscapeInterproceduralPass が escape 解析
    ↓
    Path が union type 引数に渡される → escape 検出
    ↓
    non_escape_summary に記録
    ↓
    class_storage_hint を "value" → "ref" に変更（★ここが未実装）
    ↓
emit 段: emitter が class_storage_hint = "ref" を見て gc_managed として emit
```

### 実装

`optimize_linked_program` 内で `NonEscapeInterproceduralPass` の実行後、`non_escape_summary` を参照して各クラスの `class_storage_hint` を更新する。

具体的には:
1. `non_escape_summary` からクラス型の引数が escape する関数を特定
2. escape する引数の型がクラス型なら、そのクラスの `class_storage_hint` を `"ref"` に変更
3. EAST doc のクラスノードの `class_storage_hint` を更新

### パーサーの暫定判定の除去

escape 解析 → storage_hint 反映が動作したら、`core_module_parser.py` の暫定判定（union type パラメータ検出）を除去する。

## 対象ファイル

| ファイル | 変更 |
|---------|------|
| `src/toolchain/link/global_optimizer.py` | escape 解析結果から class_storage_hint を更新するロジック追加 |
| `src/toolchain/compile/core_module_parser.py` | 暫定判定を除去 |

## 受け入れ基準

- [ ] escape 解析の結果が class_storage_hint に反映される。
- [ ] union type 引数に渡されるクラスが自動的に ref (gc_managed) になる。
- [ ] パーサーの暫定判定（union type パラメータ検出）が除去されている。
- [ ] `check_py2x_transpile --target cpp` pass。

## 子タスク

- [ ] [ID: P0-ESCAPE-TO-STORAGE-HINT-01-S1] `optimize_linked_program` で `non_escape_summary` を参照し、escape するクラス型引数の `class_storage_hint` を `"ref"` に更新する。
- [ ] [ID: P0-ESCAPE-TO-STORAGE-HINT-01-S2] `core_module_parser.py` の暫定判定を除去する。
- [ ] [ID: P0-ESCAPE-TO-STORAGE-HINT-01-S3] `Path` が escape 解析結果だけで gc_managed になることを検証する。

## 決定ログ

- 2026-03-20: `Path` の `class_storage_hint` が `value` のまま `object` に入れられない問題。パーサーで暫定検出を実装したが、正しくは escape 解析の結果を反映すべき。escape 解析結果 → storage_hint の仕組みが未整備であることが判明。P0 で起票。
