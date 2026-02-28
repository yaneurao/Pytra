# P2: Java 出力の過剰括弧削減

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-JAVA-PARENS-01`

背景:
- `sample/java` の生成コードに `double x2 = (x * x);` のような過剰な括弧が残り、可読性を下げている。
- 現行 Java emitter は二項演算を常に全体括弧で包む実装のため、優先順位が明白な式でも冗長になる。
- 括弧を一律除去すると意味変更のリスクがあるため、演算子優先順位ベースで最小括弧化する必要がある。

目的:
- Java backend の式出力を「意味保存を維持した最小括弧」に寄せ、`sample/java` の可読性を改善する。

対象:
- `src/hooks/java/emitter/java_native_emitter.py` の式出力（特に `BinOp` 周辺）
- `test/unit/test_py2java_smoke.py` と Java codegen 回帰テスト
- `sample/java` 再生成結果

非対象:
- Java backend の大規模最適化（速度改善、runtime API 再設計など）
- 他 backend（cpp/rs/cs/js/ts/go/swift/kotlin/ruby/lua）の括弧規約変更
- AST/EAST 構造そのものの再設計

受け入れ基準:
- `x * x` のような単純式で不要な全体括弧が外れ、意味が変わらないこと。
- 演算子優先順位や結合規則が絡む式では必要な括弧が維持されること。
- 既存 Java smoke/変換回帰が通過し、`sample/java` 再生成で過剰括弧が縮退すること。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2java_smoke.py' -v`
- `python3 tools/regenerate_samples.py --langs java --force`
- `rg -n \"\\(x \\* x\\)\" sample/java`

決定ログ:
- 2026-02-28: ユーザー指示により、Java 生成コードの過剰括弧削減を `P2` として起票した。

## 分解

- [ ] [ID: P2-JAVA-PARENS-01-S1-01] Java emitter の括弧出力契約（最小括弧化ルールと fail-closed 条件）を文書化する。
- [ ] [ID: P2-JAVA-PARENS-01-S2-01] `BinOp` 出力を優先順位ベースへ変更し、不要な全体括弧を削減する。
- [ ] [ID: P2-JAVA-PARENS-01-S2-02] `Compare/BoolOp/IfExp` など周辺式との組み合わせで意味保存を担保する回帰ケースを追加する。
- [ ] [ID: P2-JAVA-PARENS-01-S3-01] `sample/java` を再生成して縮退結果を確認し、回帰テストを固定する。
