# EAST仕様

## 1. 目的

- Pytra は、各言語バックエンドに分散した前処理を共通化するため、EAST（Extended AST）を導入しなければならない（MUST）。
- EAST は、Python AST から言語非依存の意味注釈付き表現へ変換する中間層でなければならない（MUST）。

## 2. 適用範囲

- EAST の対象は、Pytra が定義する Python サブセットとする（MUST）。
- Python 完全互換（動的 import、動的実行機構の完全再現）は対象外とする（MUST NOT）。

## 3. 責務境界

- EAST 生成器は、次を実施しなければならない（MUST）。
  - 構文正規化（`main` ガード抽出、識別子衝突回避、必要な一時変数導入）
  - 型解決（明示注釈 + 推論）
  - 参照特性解決（読み取り専用/可変）
  - 必要 cast の明示
- バックエンドは、EAST を入力としてコード生成を行うべきである（SHOULD）。
- 言語固有の最終判断（所有権、null、例外モデル、標準ライブラリ差分）はバックエンドが担う（MUST）。

## 4. EASTノード必須属性

- 式ノードは少なくとも次を保持しなければならない（MUST）。
  - `resolved_type`
  - `borrow_kind`（`value` / `readonly_ref` / `mutable_ref` / `move`）
  - `casts`
  - `source_span`
- 関数ノードは少なくとも次を保持しなければならない（MUST）。
  - `arg_types`
  - `return_type`
  - `arg_usage`（引数ごとの readonly/mutable）
  - `renamed_symbols`

## 5. 型システム

- EAST 内の正規型は Python 表記ベースで保持しなければならない（MUST）。
  - 基本型: `int`, `float`, `bool`, `str`, `bytes`, `bytearray`, `None`
  - 合成型: `list[T]`, `dict[K,V]`, `set[T]`, `tuple[...]`
  - 拡張型: `Path`, ユーザー定義クラス
- 各言語型への写像はバックエンド側の責務とする（MUST）。

## 6. 型推論

- 型推論は積極推論を採用してよい（MAY）。
- ただし健全性を優先し、次を満たさない推論結果を採用してはならない（MUST NOT）。
  - 型が一意に決まらない
  - 後続使用点で矛盾する
- 推論失敗時は EAST 生成を停止し、エラーを返さなければならない（MUST）。

## 7. readonly解析

- EAST 生成器は、関数引数について readonly/mutable 判定を行わなければならない（MUST）。
- readonly 判定は、少なくとも次を満たす場合にのみ成立する（MUST）。
  - 引数への再代入がない
  - 可変操作（添字代入、`append` 等）がない
  - 可変参照として外部へ渡していない
- 判定結果は `arg_usage` に保存しなければならない（MUST）。

## 8. cast

- 暗黙変換が必要な箇所は、EAST 上で明示 cast として表現しなければならない（MUST）。
- バックエンドは EAST cast 指示と矛盾する変換を行ってはならない（MUST NOT）。
- バックエンド独自 cast 追加は、EAST cast と整合する範囲で許可する（MAY）。

## 9. エラー契約

- EAST 生成エラーは、次を含まなければならない（MUST）。
  - エラー種別（推論失敗/未対応構文/意味矛盾）
  - `source_span`
  - 利用者向け修正指針（短文）

## 10. バックエンド契約

- バックエンドは EAST の `resolved_type` / `borrow_kind` / `casts` を尊重しなければならない（MUST）。
- EAST を受けたバックエンドは、言語固有の意味差分を吸収して最終コードを生成しなければならない（MUST）。

## 11. 導入計画

- Phase 1（AST+EAST併用）:
  - EAST 生成器を実装する（MUST）
  - バックエンドはブリッジ経路を維持してもよい（MAY）
- Phase 2（主要言語移行）:
  - C++/Rust/Go/Java を EAST 経路へ移行する（SHOULD）
- Phase 3（全面移行）:
  - C#/JS/TS/Swift/Kotlin を EAST 経路へ移行する（SHOULD）
  - AST直読み経路を削除する（SHOULD）

## 12. 受け入れ基準

- `test/py` 既存ケースが EAST 経由で変換可能であること（MUST）。
- 仕様差分は文書化されていること（MUST）。
- 推論失敗時エラーに位置情報と修正指針が含まれること（MUST）。
- 共通ランタイムケース（例: `math`, `pathlib`）で言語間結果一致を維持すること（SHOULD）。
