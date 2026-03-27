<a href="../../en/plans/p2-link-input-completeness.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2-LINK-INPUT-COMPLETENESS: link 層の入力完全性検証

最終更新: 2026-03-26
ステータス: 未着手

## 背景

selfhost（P2-SELFHOST-S4）で Go build が失敗している主原因は、link-input に渡す EAST3 モジュール群が不完全なこと。seed 37本から import されているが seed に含まれていない依存モジュール（6件）が欠落しており、emit 後の Go コードに未定義シンボルが発生する。

この問題は selfhost 固有ではなく、マルチモジュール Python プロジェクトを変換する際に一般的に発生する。link 層は全モジュールの情報が集まる場であり、入力の完全性をここで検証するのが設計上正しい。

## 設計

### link 層の入力完全性検証

link 層（`LinkedProgramLoader`）は `link-input.v1` を受け取った時点で、以下を検証する。

1. **import 解決検証**: 全 linked module の `meta.import_bindings` / `meta.import_modules` / `meta.import_symbols` に含まれる module_id が、link-input 内のモジュールとして存在することを確認する
2. **未解決 import の列挙**: 存在しない module_id を欠落モジュールとしてエラー報告する
3. **fail-closed**: 未解決 import が 1 件でもあれば link を停止する（暗黙的に無視しない）

エラーメッセージの形式:

```
link error: unresolved import dependency
  resolver.py imports builtin_registry (module_id: toolchain2.resolve.py.builtin_registry)
  but no link unit provides this module.

  Missing modules:
    - toolchain2.compile.jv
    - toolchain2.resolve.py.builtin_registry
    - toolchain2.resolve.py.normalize_order
    - toolchain2.parse.py.nodes
    - toolchain2.parse.py.parser
    - toolchain2.link.expand_defaults
```

### 型スタブによる補完（parse 不能モジュール向け）

依存モジュールが parse 不能な場合、link-input に投入可能な型スタブ（EAST3 形式）を提供する仕組みを用意する。

- スタブは `east_stage=3` を持つ正規の EAST3 文書だが、関数本体が空（または `raise NotImplementedError` 相当）
- 型注釈・関数シグネチャ・クラス定義のみを保持
- スタブで Go コンパイラの型チェックを通すことが目的であり、実行は想定しない
- 情報源:
  - EAST1/EAST2 が取れる場合: そこからシグネチャを自動抽出
  - parse 自体が失敗する場合: 手書き宣言ファイル（`.pyi` 相当）から生成

### 既存実装との関係

- `_analyze_import_graph_impl`（`src/toolchain2/frontends/east1_build.py` 正本）が import graph 解析の原型。これを link 層の入力検証にも活用する
- `LinkedProgramLoader` の既存責務（type_id 確定、non-escape summary 等）は変更しない。入力検証はそれらの前段として追加する

## リスク

- `pytra.std.*` / `pytra.built_in.*` 等の runtime モジュールは link-input に含めない運用がありうる。これらを「既知の外部モジュール」として検証除外するホワイトリストが必要
- 循環 import がある場合の検証順序

## サブタスク

1. [ID: P2-LINK-COMPLETE-S1] link 層で import 解決の完全性検証を実装（未解決 import を fail-closed で報告）
2. [ID: P2-LINK-COMPLETE-S2] runtime / stdlib モジュールのホワイトリスト（検証除外対象）を定義
3. [ID: P2-LINK-COMPLETE-S3] 型スタブ生成の仕組みを設計・実装（parse 不能モジュール向け）
4. [ID: P2-LINK-COMPLETE-S4] selfhost 37本に対して完全性検証を実行し、欠落モジュールを確認

## 受け入れ基準

1. link-input に不完全なモジュール群を渡した場合、欠落モジュールを列挙してエラー停止すること
2. runtime / stdlib の import は誤検出しないこと
3. 型スタブを link-input に投入すれば、link が成功すること
4. 既存の fixture / sample / selfhost パイプラインが回帰しないこと

## 決定ログ

- 2026-03-26: selfhost の Go build 失敗の根本原因が link-input の不完全性であることを特定。新しい仕組みではなく、link 層が既に持つべき入力検証として実装する方針を決定。推移的閉包の算出は link 層の責務であり、手動のファイル選定に依存しない設計とする。
