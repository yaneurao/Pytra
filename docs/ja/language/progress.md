<a href="../../en/language/progress.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# プロジェクト進捗

## バックエンドサポート状況

[fixture マトリクス](./backend-progress-fixture.md)
— 言語機能の単体テスト（146 件）。1機能1ファイルで、各ターゲット言語で emit + compile + run + stdout 一致を検証する。

[sample マトリクス](./backend-progress-sample.md)
— 実アプリケーション（18 件）。マンデルブロ集合、レイトレーシング、ゲーム・オブ・ライフ等の実用プログラムを各言語で実行し、Python と同じ出力が得られるか検証する。

[selfhost マトリクス](./backend-progress-selfhost.md)
— Pytra の変換器自身（toolchain2）を各言語に変換し、変換後のコンパイラで全言語の emit ができるか検証する。最終目標は全マス 🟩。

## タスク一覧

[TODO 索引](../todo/index.md)
— C++ / Go / Rust / TS / インフラの領域別にタスクを管理している。各 agent は自分の領域ファイルだけを読み書きする。

## 更新履歴

[![更新履歴](https://img.shields.io/badge/📋_更新履歴-全履歴を見る-2563EB?style=for-the-badge)](../changelog.md)

日単位で変更内容を記録している。仕様変更、新機能、バグ修正、ドキュメント更新を含む。

## ドキュメント

- [チュートリアル](../tutorial/README.md)
- [ガイド](../guide/README.md)
- [仕様書](../spec/index.md)
