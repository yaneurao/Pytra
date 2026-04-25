# P1-DATACLASS-OVER-JSONVAL-DICT: 一時構造体の dict[str, JsonVal] を @dataclass に置き換える

最終更新: 2026-04-25

## 背景

toolchain のコード（parse/resolve/compile/link）で、一時的なデータ受け渡しに `dict[str, JsonVal]` を多用している。これは Python では動くが、selfhost（C++ 変換）で以下の問題を引き起こす。

1. **型情報の喪失** — フィールドが `JsonVal` に埋もれ、EAST の型推論が効かない。ループ変数や get の戻り値が `unknown` になる
2. **null-only 構造の脆弱性** — 全フィールドが None の dict を C++ に変換すると `Optional<int>` や `std::nullopt` の扱いで壊れやすい
3. **共変性の暗黙依存** — `list[dict[str, JsonVal]]` を `list[JsonVal]` に入れるパターンが C++ の型チェックで弾かれる（type_norm.py / type_resolver.py で実際に発生）
4. **可読性** — `span["lineno"]` より `span.lineno` のほうが意図が明確

## 方針

- EAST ノードの走査で受け取る入力型としての `dict[str, JsonVal]` は正しい用途であり、変更しない
- toolchain 内部でデータを受け渡すために**新規作成**している `dict[str, JsonVal]` を `@dataclass` に置き換える
- 対象は emitter の手前の段（parse/resolve/compile/link）を優先する
- emitter 側は emitter-guide §1.3 で新規利用を禁止済み。既存コードは selfhost blocker に当たったものから順次移行

## 対象範囲と作業量の概算

| 層 | `dict[str, JsonVal]` 出現数 | うち入力型（走査用） | うち一時構造体（置換対象） |
|---|---|---|---|
| parse | ~139 | 多数（nodes.py の to_jv 等） | source_span, nodes の一部 |
| resolve | ~172 | 多数（resolver の EAST ノード操作） | builtin_registry の型情報、resolver 内部の中間結果 |
| compile | ~46 | 多数（lower のノード走査） | type_summary の型情報 |
| link | ~227 | 多数（linker のノード走査） | shared_types, manifest 構造 |

正確な置換対象数は各ファイルを精査して決める（S1 で実施）。

## サブタスク

### S1: 棚卸しと優先順位付け

selfhost build で実際にブロッカーになった/なりそうな箇所を洗い出し、優先順位を付ける。
既知の例:
- `SourceSpan` の null-only dict（対処済み）
- `type_norm.py` / `type_resolver.py` の `list[dict[str, JsonVal]]` vs `list[JsonVal]`（対処済み）
- `builtin_registry.py` の型情報構造

#### 2026-04-25 棚卸し結果

`rg -c "dict\\[str, JsonVal\\]" src/toolchain/{parse,resolve,compile,link}` で確認した主な出現数は以下。

| 層 | 主なファイル | 出現数 | 分類 |
|---|---:|---:|---|
| parse | `nodes.py` | 99 | ほぼ EAST JSON `to_jv()` 出力。戻り値契約なので非対象 |
| parse | `parser.py` | 33 | `ParseContext` 用 import metadata と、EAST node / meta 生成が混在 |
| resolve | `resolver.py` | 151 | 大半は EAST node 走査。内部 env / import metadata / synthetic node 生成が混在 |
| resolve | `builtin_registry.py` | 9 | 署名構造は既に `FuncSig` / `ClassSig` / `ModuleSig` へ dataclass 化済み。残りは EAST 入力 accessor |
| compile | `type_summary.py` | 20 | 型 summary payload を `dict[str, JsonVal]` で組み立てている。selfhost 型安定化の優先候補 |
| compile | `lower.py` | 18 | `ForCore` plan / meta など EAST3 node 生成。外部 JSON 契約に直結するため慎重に扱う |
| link | `linker.py` | 132 | 大半は linked EAST3 node 走査/metadata 生成。局所的 summary から順次対象 |
| link | `type_stubgen.py` | 24 | synthetic EAST3 stub 生成。JSON 出力契約なので低優先 |
| link | `shared_types.py` | 4 | `LinkedModule` は既に dataclass 化済み。残りは EAST doc accessor |

#### 優先順位

1. **S4-1: `src/toolchain/compile/type_summary.py` の summary dataclass 化**
   - `summarize_type_expr()` / `unknown_type_summary()` / `representative_json_contract_metadata()` 周辺が `Node` payload を手組みしている。
   - `kind/category/mirror/...` の固定フィールドを dataclass にし、最後に `to_jv()` で JSON 化する。
   - selfhost では型 summary が多段に流れるため、`dict[str, JsonVal]` より効果が大きい。
2. **S2-1: `src/toolchain/parse/py/parser.py` の import metadata dataclass 化**
   - `import_bindings: list[dict[str, JsonVal]]` / `qualified_refs: list[dict[str, JsonVal]]` が `ParseContext` を跨いで流れる。
   - `ImportBindingDraft` / `QualifiedRefDraft` を追加し、`_build_meta()` 直前で JSON 化する。
   - `nodes.py` の `to_jv()` は非対象のまま維持する。
3. **S3-1: `src/toolchain/resolve/py/resolver.py` の import resolution metadata dataclass 化**
   - `_build_import_resolution_meta()` / `_enhance_binding()` で `ImportBinding` 相当を dict で組み立てている。
   - parse 側 draft と同型の dataclass へ寄せると、cross-module import metadata の型が安定する。
4. **S5-1: `src/toolchain/link/linker.py` の linked-program manifest row dataclass 化**
   - `linked_program_v1.modules[]` / `manifest` / `diagnostics` など、出力用 row を一時 dataclass に寄せる。
   - node 走査用 `dict[str, JsonVal]` は非対象。
5. **S2/S3/S5 継続: synthetic EAST node builder は最後**
   - `type_stubgen.py` / `lower.py` の node 生成は EAST JSON 契約そのものなので、型安定化より regression risk が高い。
   - 置換する場合も builder dataclass ではなく、小さな typed helper 関数を先に整える。

#### 非対象として固定するもの

- `nodes.py` の `to_jv()` 戻り値と、EAST node を受け取る `dict[str, JsonVal]` 引数。
- `jv_dict()` / `_dict_get_obj()` 系の JSON accessor。
- `type_id.py` / `trait_id.py` の class node walker。ここは EAST3 JSON 走査が本質。
- `type_stubgen.py` の `_module_doc()` など synthetic EAST3 出力 builder。必要時は別タスクで builder helper を設計する。

### S2: parse 層の @dataclass 化

`src/toolchain/parse/py/` 配下の一時構造体を `@dataclass` に置き換える。
`nodes.py` は既に `@dataclass` を使っているが、`to_jv()` の内部で `dict[str, JsonVal]` を返す経路が残っている。

### S3: resolve 層の @dataclass 化

`src/toolchain/resolve/py/` 配下。`resolver.py` (153箇所) が最大だが、大部分は EAST ノード走査の入力型。内部の中間結果構造を `@dataclass` に切り替える。

### S4: compile 層の @dataclass 化

`src/toolchain/compile/` 配下。`type_summary.py` (20箇所) の型情報構造が主な対象。

### S5: link 層の @dataclass 化

`src/toolchain/link/` 配下。`linker.py` (133箇所) が最大だが、走査用が大半。`shared_types.py`, `type_stubgen.py` の内部構造が対象。

## 非対象

- EAST ノードの走査で受け取る入力型としての `dict[str, JsonVal]` — これは JSON 由来の EAST データの表現であり、変更しない
- emitter 層 — emitter-guide §1.3 で新規禁止済み。既存の移行は各 backend 担当の selfhost 作業で漸進的に実施
- `to_jv()` の戻り値型変更 — EAST の JSON シリアライズ契約に関わるため、別タスクで判断

## 制約

- `@dataclass` は selfhost 対象コードで使用可能（`from dataclasses import dataclass` は no-op import として許可済み）
- 新規 `@dataclass` は `src/toolchain/` 配下の適切なモジュールに配置する
- 既存のテストや golden が壊れないよう、外部 API（EAST JSON 出力）は変えない

## 決定ログ

- 2026-04-25: 起票。selfhost の null-only dict / covariance 系ブロッカーの根本対策として、一時構造体の `@dataclass` 化を進める方針を決定。emitter-guide §1.3 に新規利用禁止ルールを追加済み。
- 2026-04-25: S1 棚卸し完了。優先度 1 の先行実装として `type_summary.py` に内部用 `TypeSummary` dataclass を追加し、`summarize_type_expr()` / `unknown_type_summary()` の payload 組み立てを dataclass 経由に変更した。戻り値は従来どおり `Node` のまま維持。
- 2026-04-25: S2 完了。`parser.py` の import metadata draft を `ImportBindingDraft` / `QualifiedSymbolRefDraft` に置換し、`_build_meta()` 直前で JSON 化する形に変更した。`nodes.py` の `to_jv()` と外部 EAST JSON metadata 形状は維持。
- 2026-04-25: S3 完了。`resolver.py` の import resolution binding 拡張を `ImportResolutionBinding` dataclass に集約し、implicit builtin binding 生成と runtime metadata 付与を JSON 境界の手前で行う形に変更した。
- 2026-04-25: S4 完了。`lower.py` の target/iter plan draft を `TargetPlanDraft` / `RuntimeIterPlanDraft` / `StaticRangePlanDraft` に置換した。compile 層に残る EAST node builder / JSON accessor は非対象として固定。
- 2026-04-25: S5 完了。`linker.py` の `linked_program_v1` / manifest module entry / manifest global / diagnostics を draft dataclass 経由で生成する形に変更した。synthetic EAST node builder は非対象として維持。
