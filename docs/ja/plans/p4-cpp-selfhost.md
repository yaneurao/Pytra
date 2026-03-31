<a href="../../en/plans/p4-cpp-selfhost.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P4-CPP-SELFHOST: C++ emitter で toolchain2 を C++ に変換し g++ build を通す

最終更新: 2026-03-31
ステータス: 進行中（S0-S2 完了、S3 未完了）

## 背景

Pytra の変換器自身（toolchain2）を C++ に変換し、変換後の C++ コンパイラが正しく動作することを検証する。これにより:

- C++ emitter の品質が toolchain2 規模のコードで検証される
- selfhost マトリクスの C++ 行が埋まる
- 将来的に C++ バイナリで高速なコンパイルが可能になる

## フロー

1. `pytra-cli2 -build --target cpp` で toolchain2 全 `.py` を C++ に変換
2. `g++` でコンパイルしてバイナリを生成
3. バイナリで fixture/sample を変換し、Python と同じ出力が得られるか検証（P3-SELFHOST-PARITY）

## サブタスク

1. [S0] selfhost 対象コードの型注釈補完（P6-GO-SELFHOST-S0 と共通）
2. [S1] toolchain2 → C++ emit + g++ build 通過 ✅
3. [S2] build 失敗の emitter/runtime 修正 ✅
4. [S3] selfhost 用 C++ golden 配置 + 回帰テスト

## 設計判断

- EAST の workaround 禁止。build 失敗は emitter/runtime の修正で解消する
- 型注釈補完（S0）は Go selfhost と共有。先に完了した側の成果を使う
- golden は `test/selfhost/cpp/` に配置し、回帰テストとして維持する

## 決定ログ

- 2026-03-29: P4-CPP-SELFHOST を起票。P3-COMMON-RENDERER-CPP 完了後に着手。
- 2026-03-30: S1（emit + build 通過）、S2（build 失敗修正）完了。tuple subscript 検出拡張、py_dict_set_mut 追加、object→str/container 型強制、前方宣言二段階出力等。
- 2026-03-31: S0 を監査で完了。`src/toolchain2/` 全 `.py` を `ast` 走査し、戻り値注釈欠落が 0 件であることを確認。回帰防止として `tools/unittest/selfhost/test_selfhost_return_annotations.py` を追加。
