<a href="../../en/spec/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# 仕様書（入口）

### ユーザー向け

| 内容 | リンク | 説明 |
|---|---|---|
| 利用仕様 | [spec-user.md](./spec-user.md) | 使い方、入力制約、テスト実行方法 |
| Python 互換性 | [spec-python-compat.md](./spec-python-compat.md) | Python との違い、使えない構文 |
| pylib モジュール | [spec-pylib-modules.md](./spec-pylib-modules.md) | 使えるモジュールと関数の一覧 |

### 言語仕様

| 内容 | リンク | 説明 |
|---|---|---|
| 型システム・type_id | [spec-type_id.md](./spec-type_id.md) | 単一継承、isinstance、POD exact match |
| tagged union | [spec-tagged-union.md](./spec-tagged-union.md) | `type X = A \| B` の宣言、コード生成 |
| Trait | [spec-trait.md](./spec-trait.md) | `@trait` / `@implements`、pure interface |
| 例外処理 | [spec-exception.md](./spec-exception.md) | raise/try/except、native_throw と union_return |
| Boxing/Unboxing | [spec-boxing.md](./spec-boxing.md) | Any/object 境界の型変換 |
| GC | [spec-gc.md](./spec-gc.md) | RC ベースの GC 方針 |

### EAST（中間表現）

| 内容 | リンク | 説明 |
|---|---|---|
| EAST 統合仕様 | [spec-east.md](./spec-east.md) | 現行正本。型推論、ノード仕様、ナローイング |
| EAST1 | [spec-east1.md](./spec-east1.md) | parse 出力契約（型未解決） |
| EAST2 | [spec-east2.md](./spec-east2.md) | resolve 出力契約（型確定） |
| EAST3 Optimizer | [spec-east3-optimizer.md](./spec-east3-optimizer.md) | 最適化パスの責務と契約 |
| Linker | [spec-linker.md](./spec-linker.md) | multi-module 連結、type_id 確定 |

### Backend / Emitter

| 内容 | リンク | 説明 |
|---|---|---|
| Emitter ガイドライン | [spec-emitter-guide.md](./spec-emitter-guide.md) | 全 emitter 共通の契約、禁止事項 |
| 言語プロファイル | [spec-language-profile.md](./spec-language-profile.md) | Lowering プロファイル、CommonRenderer |
| runtime mapping | [spec-runtime-mapping.md](./spec-runtime-mapping.md) | mapping.json のフォーマット |
| ランタイム | [spec-runtime.md](./spec-runtime.md) | ランタイム配置、include 規約 |
| C++ Optimizer | [spec-cpp-optimizer.md](./spec-cpp-optimizer.md) | C++ backend 後段最適化 |
| C++ list 参照 | [spec-cpp-list-reference-semantics.md](./spec-cpp-list-reference-semantics.md) | C++ list の alias/共有/破壊的更新 |

### 言語別 Backend 契約

| 内容 | リンク | 説明 |
|---|---|---|
| Java | [spec-java-native-backend.md](./spec-java-native-backend.md) | Java native backend 契約 |
| Lua | [spec-lua-native-backend.md](./spec-lua-native-backend.md) | Lua native backend 契約 |
| Zig | [spec-zig-native-backend.md](./spec-zig-native-backend.md) | Zig native backend 契約 |
| 言語別一覧 | [language/index.md](../language/index.md) | 言語ごとの機能対応状況 |

### 開発者向け

| 内容 | リンク | 説明 |
|---|---|---|
| 実装仕様 | [spec-dev.md](./spec-dev.md) | 実装方針、モジュール構成 |
| フォルダ責務 | [spec-folder.md](./spec-folder.md) | どのフォルダに何を置くか |
| stdlib 正本化 | [spec-stdlib-signature-source-of-truth.md](./spec-stdlib-signature-source-of-truth.md) | pytra/std を型仕様の正本にする契約 |
| Codex 運用 | [spec-codex.md](./spec-codex.md) | Codex の作業ルール、TODO 運用 |
| 開発思想 | [spec-philosophy.md](./spec-philosophy.md) | EAST 中心設計の背景 |
| 旧仕様 | [archive/index.md](./archive/index.md) | 退役した仕様のアーカイブ |

## Codex 起動時の確認先

- Codex は起動時に `docs/ja/spec/index.md` を入口として読み、続けて [Codex 向け運用仕様](./spec-codex.md) と [TODO](../todo/index.md) を確認します。
