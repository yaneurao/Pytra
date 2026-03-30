<a href="../../en/plans/p0-east3-narrowing-cast.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0-EAST3-NARROWING-CAST: isinstance narrowing 後に Cast/Unbox ノードを挿入する

最終更新: 2026-03-30
ステータス: 未着手

## 背景

EAST3 は isinstance narrowing 後に `resolved_type` を更新するが、明示的な Cast/Unbox ノードを挿入しない。例えば:

```python
val: JsonVal = json.loads(data)
if isinstance(val, str):
    print(val.upper())  # val は str にナローイングされている
```

EAST3 では `val` の `resolved_type` が `str` に更新されるが、式ノードとしては元の `Name("val")` のまま。Rust のように `PyAny` から具象型へのダウンキャストが必要な言語では、emitter が「この Name の `resolved_type` と元の宣言型が違う → 変換呼び出しを挿入」というロジックを自前で持つしかなく、emitter guide §1.1 違反になる。

## 現状

- spec-east.md §7.1: narrowing は resolve 段の型環境更新で実現し、新しい EAST ノードは導入しないと規定
- Rust emitter: `_emit_name` に `EAST3 DEFICIENCY WORKAROUND` コメント付きで workaround を実装
- C++/Go/TS: 暗黙キャストが効くので問題が顕在化していない

## 提案

isinstance narrowing で `resolved_type` が変わった Name 参照を **Cast ノードで包む**。

```json
// 現状: Name の resolved_type だけ更新
{"kind": "Name", "id": "val", "resolved_type": "str"}

// 提案: Cast ノードで包む
{"kind": "Cast", "value": {"kind": "Name", "id": "val", "resolved_type": "JsonVal"}, "to": "str", "reason": "isinstance_narrowing"}
```

- 元の Name は宣言時の型（`JsonVal`）を保持
- Cast ノードが narrowing 後の型（`str`）への変換を明示
- emitter は Cast ノードをレンダリングするだけ（§1.1 準拠）

## 修正箇所

`src/toolchain2/compile/east2_to_east3_lowering.py` または `src/toolchain2/resolve/` の narrowing 処理。

narrowing で `resolved_type` を更新する際に、元の型と異なる場合のみ Cast ノードを挿入する。元の型と同じ場合（redundant cast）は挿入しない。

## 影響範囲

- Cast ノードが増えるので、全言語の emitter が Cast ノードをレンダリングできる必要がある（ほとんどは既に対応済み）
- C++/Go/TS は暗黙キャストで動いていたので、明示 Cast が増えても出力は変わらない（implicit_promotions で Cast 出力がスキップされる場合もある）
- Rust は workaround を削除して Cast ノードのレンダリングに置き換える
- spec-east.md §7.1 の「新しい EAST ノードは導入しない」を「Cast ノードで包む」に更新する必要がある

## 決定ログ

- 2026-03-30: Rust emitter の `_emit_name` に narrowing workaround が §1.1 違反として発見。EAST3 側で Cast ノードを挿入する方針に決定。Rust 担当が EAST3 修正を担当する。
