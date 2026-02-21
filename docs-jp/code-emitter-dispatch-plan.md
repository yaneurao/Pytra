# CodeEmitter 共通ディスパッチ再設計メモ

最終更新: 2026-02-21

## 背景

- selfhost 版 C++ では `CodeEmitter` のメソッド呼び出しが static 束縛になり、Python 側の「派生で上書きすれば動く」前提をそのまま移せない。
- そのため `render_expr` / `emit_stmt` の共通化を進めると、派生実装（`CppEmitter`）へ到達しない経路が発生する。

## 方針

- virtual 依存を増やさず、`EmitterHooks` の注入点を増やして段階移行する。
- 共通基底で「最小ディスパッチ」だけ行い、言語固有分岐は hook と profile へ寄せる。
- selfhost では hook 不在でも動くフォールバックを `CppEmitter` 側に残し、差分検証で徐々に削る。

## 段階計画

1. `render_expr` の kind ごとに hook ポイントを追加する。
2. `emit_stmt` も同様に kind ごとの hook ポイントへ分解する。
3. `CppEmitter` は hook 優先 + fallback の二段構成に統一する。
4. `tools/check_selfhost_cpp_diff.py` で差分ゼロを維持しながら fallback を縮退する。
5. fallback が十分に減った段階で、共通ディスパッチを `CodeEmitter` 本体へ戻す。

## 受け入れ基準

- Python 実行パス: `hooks` 有効時に既存ケースのコード生成結果が不変。
- selfhost 実行パス: `mismatches=0` を維持。
- `py2cpp.py` の `render_expr` / `emit_stmt` 本体分岐が段階的に短くなる。

## py2cpp / py2rs 共通化候補（2026-02-22）

- 優先 A（まず `CodeEmitter` へ移す）
  - `If` / `While` / `ForRange` / `For` の文スケルトン生成（開閉ブロック + scope push/pop）
  - `Assign` / `AnnAssign` / `AugAssign` の「宣言判定 + 代入先レンダ」共通骨格
  - `Compare` / `BoolOp` / `IfExp` の式組み立て
  - import 束縛テーブル読み込み（`meta.import_bindings` 反映）
- 優先 B（次段）
  - 型名正規化 + 言語型への最終写像 (`normalize_type_name` 後段)
  - `Call` 前処理（`_prepare_call_parts` 結果の共通利用）
  - `Tuple` 代入の一時変数 lower
- 優先 C（最後）
  - 言語別ランタイム関数へのルーティング（profile + hooks）
  - 文字列/配列の細かい最適化（演算子簡約・括弧削減）

## 進捗メモ（2026-02-22）

- `CodeEmitter.render_boolop_common()` を追加し、`py2rs` / `py2js` / `py2cs` の `BoolOp` 生成を共通化した。
- `CodeEmitter.render_compare_chain_common()` を追加し、`py2rs` / `py2js` / `py2cs` の `Compare` 連鎖生成を共通化した。
