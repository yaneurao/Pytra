# P2: immutable 引数言語向けの引数リネーム共通メソッド

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-MUTABLE-PARAM-RENAME`

## 背景

Python では引数への再代入が合法（引数は単なるローカル変数）だが、Zig/Rust/Swift ではパラメータが immutable であり、再代入するにはローカル変数にコピーする必要がある。

各 emitter が個別にリネーム規則を実装すると命名がバラバラになる。`CodeEmitter` に共通メソッドを追加し、統一された規則で処理する。

## 設計

共通ロジックを `CodeEmitter` のメソッド **かつ** スタンドアロン関数として提供:

- `_collect_reassigned_params(func_def)` → FunctionDef body を走査し、引数名に再代入がある名前の set を返す
- `_mutable_param_name(name)` → リネーム後の名前を返す（`name` → `name_`）

`CodeEmitter` を継承している emitter はメソッドとして呼び、継承していない emitter（Swift, Julia, Dart, Zig 等）はスタンドアロン関数として呼ぶ。

immutable 引数の言語の emitter は FunctionDef emit 時に:
1. `_collect_reassigned_params` で再代入される引数を検出
2. 引数名を `_mutable_param_name` でリネーム
3. 関数先頭で `var name = name_` 等のコピー文を生成

### 備考

- Rust は `mut arg: T` で引数を mutable にできるため、リネーム不要（既に対応済み）
- 大半の emitter が `CodeEmitter` を継承していない設計問題がある。将来的に全 emitter を `CodeEmitter` 継承に統一するか、共通ロジックをスタンドアロンモジュールに切り出す方針は別タスクで検討。

## 対象

| ファイル | 変更内容 |
|---|---|
| `code_emitter.py` | `_collect_reassigned_params` / `_mutable_param_name` 追加（メソッド + スタンドアロン） |
| Zig emitter | 共通メソッド/関数を呼ぶように修正 |
| Swift emitter | 同上 |

## 子タスク

- [x] [ID: P2-MUTABLE-PARAM-RENAME-01] `CodeEmitter` に共通メソッドを追加する（実装済み、Zig は暫定対応済み）
- [ ] [ID: P2-MUTABLE-PARAM-RENAME-02] Swift emitter を共通関数呼び出しに修正する
- [ ] [ID: P2-MUTABLE-PARAM-RENAME-03] スタンドアロン関数版を `code_emitter.py` に公開する

## 決定ログ

- 2026-03-22: Zig 担当が引数再代入問題を報告。Rust/Swift/Zig で統一した命名規則を `CodeEmitter` 共通メソッドとして提供する方針で起票。
