<a href="../../en/plans/p1-tagged-union-all-backends.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: `type X = A | B | ...` のタグ付きunion struct 全バックエンド対応

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-TAGGED-UNION-ALL-BACKENDS-01`

## 背景

現在 C++ バックエンドでは `type X = A | B` を `std::variant` に変換しているが、
`std::variant` は再帰型（例: JSON の `type JsonVal = None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]`）を表現できない。

全バックエンドで再帰型を含む union 型を統一的に扱うため、
`type X = A | B | ...` 宣言をタグ付き struct（tagged union）として emit する仕組みを導入する。

## 各言語での emit 戦略

| 言語 | 機構 | 再帰型 |
|------|------|--------|
| C++ | tagged struct（全フィールド展開） | `rc<list<T>>` 等で可 |
| Rust | `enum` | `Vec`/`Box` 経由で自然に可 |
| Swift | `indirect enum` | `indirect` キーワードで可 |
| Kotlin/Java | sealed class | 参照型なので自然に可 |
| Scala | sealed trait + case class | 同上 |
| TypeScript | discriminated union | 動的なので問題なし |
| Go | struct + tag | slice/map がポインタなので可 |
| C# | abstract record + derived records | 参照型なので可 |
| Nim | object variant | `case` で可 |
| Lua/PHP/Ruby | 動的型 | テーブル/連想配列で表現 |

## 対象

- `type X = A | B | ...` 宣言のパース（P1-TYPE-ALIAS-SUPPORT-01 で実装済み）
- EAST3 IR の TypeAlias ノードから各バックエンドが tagged union を生成する emit パス
- C++ バックエンド: `std::variant` → tagged struct への切り替え
- 非 C++ バックエンド: 各言語ネイティブの tagged union 生成
- isinstance / パターンマッチの tag ベース判定への対応

## 非対象

- C++ union 最適化（メモリレイアウト最適化）— 後続タスクで `--cpp-opt-pass union-layout` 等のオプションとして対応
- Generic type alias（`type Stack[T] = list[T]`）— 対象外

## 修正方針

### フェーズ 1: C++ バックエンド

1. `type X = A | B | ...` 宣言から tagged struct を生成する emit パスを追加
2. 既存の `std::variant` 生成を tagged struct に置き換え
3. コンストラクタ（`make_*` static メソッド or ファクトリ関数）を自動生成
4. isinstance 判定を tag ベースに変換
5. json.py を `type JsonVal = ...` で書き直して動作確認

### フェーズ 2: 他バックエンド

各バックエンドの言語ネイティブな tagged union に emit を拡張。

### フェーズ 3（将来）: C++ union 最適化

CLI オプションで tagged struct のフィールドレイアウトを union 化し、メモリ効率を改善。
特殊メンバ関数（デストラクタ、コピー/ムーブ）の自動生成が必要。

## 受け入れ基準

- `type JsonVal = None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]` が全対象バックエンドで正しく emit される。
- 再帰型を含む union が transpile・コンパイル（C++）可能。
- 既存の非再帰 union（argparse の `ArgValue` 等）も tagged struct 経由で動作する。
- fixture / sample pass、selfhost mismatches=0。

## 決定ログ

- 2026-03-18: ユーザー提案。`std::variant` の再帰型制約が JSON 等の表現を阻害。tagged struct を全バックエンドで統一的に使う方針を決定。
- 2026-03-18: C++ union 最適化は将来の CLI オプションとして分離。まずは全フィールド展開の tagged struct で実装する。
- 2026-03-18: C++ バックエンド先行実装完了。named type alias（`type X = A | B | ...`）を tagged struct として emit。inline union（名前なし）は `std::variant` を維持。header_builder / cpp_emitter 両方で対応。暗黙変換コンストラクタ付き（bool は Tag 引数で曖昧さ回避）。None チェックは tag ベース判定に変更。242 test pass。他バックエンドは後続タスクとする。
