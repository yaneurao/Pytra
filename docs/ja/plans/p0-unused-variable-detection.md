# P0: 未使用変数の検出・除去

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-UNUSED-VAR`

## 背景

Python では問題にならない未使用変数（代入後に一度も参照されない）がそのまま EAST3 に残り、Zig では `unused local` コンパイルエラー、C++ では `-Werror=unused-variable` で問題になる。各 emitter で個別に未使用検出するのは重複。

## 設計

EAST3 の FunctionDef body を走査し、代入後に一度も参照されない変数に `unused: true` フラグを付与する。emitter はこのフラグを見て `_ = var` 等の抑制コードを生成するか、宣言自体を省略する。

## 子タスク

- [ ] [ID: P0-UNUSED-VAR-01] 未使用変数検出パスを実装し、Assign target / VarDecl に `unused` フラグを付与する
- [ ] [ID: P0-UNUSED-VAR-02] ユニットテストを追加する

## 決定ログ

- 2026-03-22: Zig 担当が sample 16 の `lr = 0.35` 等で unused エラーを報告。全 backend 共通。
