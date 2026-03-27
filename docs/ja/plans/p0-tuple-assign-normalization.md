<a href="../../en/plans/p0-tuple-assign-normalization.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: タプル代入（swap/destructuring）のノード正規化

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-TUPLE-ASSIGN-NORM`

## 背景

`values[j], values[j+1] = values[j+1], values[j]` のようなタプル代入が単なる `Assign(target=Tuple, value=Tuple)` として表現される。Swap パターンなのか一般的なタプル代入なのか emitter 側で判別が必要。

EAST3 には既に `Swap` ノードが存在する（C++ emitter が 2 変数の Name swap に使用）。Subscript を含む swap にも拡張すべき。

## 設計

EAST3 lowering で:
1. `Assign(target=Tuple([a, b]), value=Tuple([b, a]))` パターンを検出
2. `Swap(lhs=a, rhs=b)` ノードに変換（Subscript 含む）
3. 3 要素以上のタプル代入は一時変数を使った展開に正規化

## 子タスク

- [ ] [ID: P0-TUPLE-ASSIGN-NORM-01] 2 要素 swap パターンを検出して Swap ノードに変換する
- [ ] [ID: P0-TUPLE-ASSIGN-NORM-02] ユニットテストを追加する

## 決定ログ

- 2026-03-22: Zig 担当がタプル代入の swap 検出を emitter 側で実装する手間を報告。全 backend 共通。
