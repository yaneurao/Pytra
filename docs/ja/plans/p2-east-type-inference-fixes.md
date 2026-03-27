<a href="../../en/plans/p2-east-type-inference-fixes.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: EAST 型推論改善（Java 担当提案 4 件）

最終更新: 2026-03-23

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-EAST-TYPE-FIX`

## 背景

Java 担当から EAST3 の型情報に関する 4 件の改善提案があった。調査の結果、根本原因は 2 箇所に集約される。

## 根本原因

### 原因 A: Assign の tuple target で name_types が更新されない

`core_stmt_parser.py:1061-1064` で `target.kind == "Name"` の場合のみ `name_types[nm] = decl_type` を更新しているが、Tuple target の場合は要素の型が `name_types` に反映されない。

これにより：
- `x, y = stack[-1]` で `stack: list[tuple[int, int]]` → value.resolved_type は `tuple[int64,int64]` だが、x, y の resolved_type が `unknown`
- 後続の `nx = x + dx` で `x` が `unknown` → `nx` も `unknown`
- VarDecl nx の type が `object`

→ Bug 2, 3, 4 の根本原因。

### 原因 B: math.* の module attribute call で複雑な式の resolved_type が unknown

`import math; math.sin((x + t * 2.0) * 0.045)` のような複雑な式で、Call ノードの resolved_type が `unknown` になる。単純な `math.sqrt(x)` では正しく `float64` が返る。

→ Bug 1 の原因（内側の式の resolved_type が unknown で、外側の Call も unknown になる連鎖）。

## 変更計画

### S1: tuple target の name_types 更新

`core_stmt_parser.py` の Assign 処理で、Tuple target の場合に value の resolved_type から要素型を抽出して `name_types` に登録する。

### S2: VarDecl type の value.resolved_type fallback

`east2_to_east3_block_scope_hoist.py` の `_resolve_assign_type()` で、target.resolved_type も annotation もない場合に value.resolved_type を使う fallback を追加。（S1 が解決すれば多くのケースで不要になるが、安全ネットとして）

### S3: math.* の resolved_type 修正

S1 が解決すれば、内側の式の型が正しくなり、math.sin/cos/sqrt の引数の resolved_type が伝搬して Call の resolved_type も正しくなる可能性が高い。S1 後に再検証し、残存していれば追加修正する。

## 決定ログ

- 2026-03-23: Java 担当の 4 提案を受領。調査の結果、根本原因は「tuple target の name_types 未更新」と「math.* の連鎖的 unknown」の 2 点に集約。
- 2026-03-23: S1 完了。`core_stmt_parser.py` の tuple destructure assign 処理で、value.resolved_type が `tuple[T1,T2]` の場合に要素型を `name_types` に登録。sample 13 の `nx`/`ny` が `int64` に解決。
- 2026-03-23: S3 完了。`core_expr_attr_call_annotation.py` で `_SH_IMPORT_SYMBOLS` も import module として認識。`from pytra.std import math` スタイルで `math.sin()` 等の resolved_type が `float64` に解決。sample 10 の全 5 math calls が修正。
- 2026-03-23: S2 は S1+S3 で自動解決。全 sample で VarDecl object/unknown と Assign unknown decl_type がゼロ。Bug 4 (decl_type unknown) も自動解決。
