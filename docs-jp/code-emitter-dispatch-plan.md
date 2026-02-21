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
