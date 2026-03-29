<a href="../../en/progress/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# プロジェクト進捗

Pytra の開発状況を一覧できるページです。各ターゲット言語のテスト結果、タスク、更新履歴、ドキュメントへのリンクをまとめています。

## フロントエンド（言語共通パイプライン）

[EAST の仕組み](../guide/east-overview.md)
— Python コードが EAST1 → EAST2 → EAST3 と変換される過程を具体例で追うガイド。初めて読む人向け。

[emitter の仕組み](../guide/emitter-overview.md)
— EAST3 がどう C++/Go/Rust 等のコードに変換されるか、変換前後を並べて解説するガイド。

[EAST 統合仕様](../spec/spec-east.md) / [EAST1](../spec/spec-east1.md) / [EAST2](../spec/spec-east2.md) / [EAST3 Optimizer](../spec/spec-east3-optimizer.md) / [Linker](../spec/spec-linker.md)
— 各段の正式仕様。

## バックエンドサポート状況

[fixture マトリクス](./backend-progress-fixture.md)
— 言語機能の単体テスト（146 件）。1機能1ファイルで、各ターゲット言語で emit + compile + run + stdout 一致を検証する。

[sample マトリクス](./backend-progress-sample.md)
— 実アプリケーション（18 件）。マンデルブロ集合、レイトレーシング、ゲーム・オブ・ライフ等の実用プログラムを各言語で実行し、Python と同じ出力が得られるか検証する。[サンプル一覧](../tutorial/samples.md)を参照。

[selfhost マトリクス](./backend-progress-selfhost.md)
— Pytra の変換器自身（toolchain2）を各言語に変換し、変換後のコンパイラで全言語の emit ができるか検証する。

## タスク一覧

[TODO 索引](../todo/index.md)
— C++ / Go / Rust / TS / インフラの領域別にタスクを管理している。各 agent は自分の領域ファイルだけを読み書きする。

## 更新履歴

[更新履歴](../changelog.md)
— 日単位で変更内容を記録している。仕様変更、新機能、バグ修正、ドキュメント更新を含む。

## ドキュメント

- [チュートリアル](../tutorial/README.md)
- [ガイド](../guide/README.md)
- [仕様書](../spec/index.md)
