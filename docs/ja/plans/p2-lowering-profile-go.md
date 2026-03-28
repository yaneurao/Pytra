# P2-LOWERING-PROFILE-GO: Go backend の Lowering プロファイル適用

最終更新: 2026-03-28
ステータス: 未着手

## 背景

Lowering プロファイル（spec-language-profile.md §7）と EAST3 言語別 lowering（tuple_unpack_style, container_covariance, with_style, property_style）は C++ 側では実装済みだが、Go 側はまだ適用されていない。

Go emitter が selfhost で詰まっている問題（tuple unpack、container covariance、with 文、@property）の多くは、lowering プロファイルが Go に適用されれば解消する。

## サブタスク

1. [ID: P2-LOWERING-GO-S1] Go の `tuple_unpack_style: "multi_return"` を EAST3 lowering に適用する — tuple unpack を `MultiAssign` に展開し、Go emitter が `x, y := f()` として写像できるようにする。関数の戻り値型を `multi_return[A, B]` に正規化する
2. [ID: P2-LOWERING-GO-S2] Go の `container_covariance: false` を EAST3 lowering に適用する — `list[str]` → `list[JsonVal]` 等の型変換を `CovariantCopy` ノードに展開し、Go emitter が要素ごとコピーループを生成する
3. [ID: P2-LOWERING-GO-S3] Go の `with_style: "defer"` を EAST3 lowering に適用する — `With` ノードを Go の `defer` パターンに適した形に展開する
4. [ID: P2-LOWERING-GO-S4] Go の `property_style: "method_call"` を EAST3 lowering に適用する — `attribute_access_kind: "property_getter"` を括弧付きメソッド呼び出しに正規化する
5. [ID: P2-LOWERING-GO-S5] Go の既存 fixture + sample parity が維持されることを確認する

## 受け入れ基準

1. Go emitter が `tuple_unpack_style` に従って多値返却で tuple unpack を処理すること
2. container covariance の型変換が Go で正しく動作すること
3. `with` 文が Go の `defer` に写像されること
4. `@property` アクセスが Go で括弧付きメソッド呼び出しになること
5. 既存 fixture + sample の Go parity が維持されること

## 決定ログ

- 2026-03-28: P2-LOWERING-PROFILE は C++ 側のみ完了して閉じられた。Go 側の lowering プロファイル適用を別タスクとして起票。
