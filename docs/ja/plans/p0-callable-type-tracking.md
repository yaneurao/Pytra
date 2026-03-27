<a href="../../en/plans/p0-callable-type-tracking.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: Callable 型の追跡

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CALLABLE-TYPE-TRACKING`

## 背景

関数引数が `Callable` 型の場合、EAST3 の `resolved_type` が `unknown` になり、emitter が関数参照と通常変数を区別できない。PowerShell では scriptblock として渡す必要があり、他の言語でも関数ポインタ/ラムダの扱いが変わる。

EAST1 パーサーが `Callable` 型注釈を認識し、`resolved_type` に `callable[..., RetType]` を設定すれば、emitter が適切なコードを生成できる。

## 子タスク

- [ ] [ID: P0-CALLABLE-TYPE-TRACKING-01] EAST1 パーサーで `Callable` 型注釈を `resolved_type` に反映する
- [ ] [ID: P0-CALLABLE-TYPE-TRACKING-02] ユニットテストを追加する

## 決定ログ

- 2026-03-22: PS 担当が Callable 引数の型追跡不足を報告。全 backend 共通の改善として起票。
