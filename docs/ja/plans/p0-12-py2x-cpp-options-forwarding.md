<a href="../../en/plans/p0-12-py2x-cpp-options-forwarding.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0-12: pytra-cli.py が C++ 固有オプションを toolchain/emit/cpp/cli.py に転送しない

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PY2X-CPP-OPTIONS-01`

## 背景

toolchain フォルダ構成変更により `backends/cpp/cli.py` → `toolchain/emit/cpp/cli.py` に移動。
pytra-cli.py は C++ emit を `toolchain/emit/cpp.py`（stripped-down）に委譲するようになり、
旧 `cli.py` が受け付けていた以下の C++ 固有オプションを pytra-cli.py が認識しなくなった。

- `--emit-runtime-cpp`
- `--multi-file` / `--single-file`
- `--dump-deps` / `--dump-options`
- `--guard-profile`, `--max-*` 系ガードリミット
- `--no-main`, `--top-namespace`
- `--from-link-output`（pytra-cli.py では定義されているが test_py2cpp_features.py の一部テストが別パスで失敗）

これにより `test_py2cpp_features.py` の CLI テスト群が
`error: unknown option: --multi-file` 等で大量失敗する。

## 対象

- `test/unit/backends/cpp/test_py2cpp_features.py` — CLI subprocess テストを `toolchain/emit/cpp/cli.py` 直接呼び出しに変更
- `test/unit/backends/cpp/test_cpp_optimizer_cli.py` — 同様の修正

## 非対象

- pytra-cli.py 自体への C++ 固有オプション追加（後続改善タスクで対応）

## 受け入れ基準

- [ ] `test_py2cpp_features.py` の `error: unknown option` 起因テストが全てパスする
- [ ] `test_cpp_optimizer_cli.py` の 2 件がパスする

## 子タスク

- [ ] [ID: P0-PY2X-CPP-OPTIONS-01] CLI テストを `toolchain/emit/cpp/cli.py` 直接呼び出しに変更

## 決定ログ

- 2026-03-21: pytra-cli.py の C++ emit パスが stripped-down `toolchain/emit/cpp.py` に変わり、C++ 固有オプションが転送されなくなったと判明。テスト側で `toolchain/emit/cpp/cli.py` を直接呼ぶよう変更する方針を採用。
