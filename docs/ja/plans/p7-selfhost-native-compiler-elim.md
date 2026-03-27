<a href="../../en/plans/p7-selfhost-native-compiler-elim.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P7: native/compiler/ を完全削除し selfhost を Python シェルアウトなしで動作させる

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01`

## 背景

`src/runtime/cpp/native/compiler/` は 4 ファイル（`transpile_cli.cpp/h`、`backend_registry_static.cpp/h`）から成り、selfhost バイナリが自分自身ではできない処理をホスト Python に委譲するためのシェルアウトブリッジである。

```
transpile_cli.cpp:
  .py 入力 → python3 -c "from toolchain.frontends import load_east3_document_typed..."
              → EAST3 JSON を /tmp に書き出し → 読み返す

backend_registry_static.cpp:
  emit_source_typed → python3 src/east2x.py ... --target cpp
                    → 生成 C++ を /tmp に書き出し → 読み返す
```

これらは selfhost が完成していないことを示す bootstrap shim であり、C++ runtime の一部ではない。

`native/README.md` にも `native/compiler/` は正規配置として記載されていない。

### シェルアウトが必要な理由

| シェルアウト先 | 阻んでいるもの |
|---|---|
| `toolchain.frontends.load_east3_document_typed` | Python AST パーサー（`ast.parse` 等）が未 transpile |
| `src/east2x.py --target cpp`（= `toolchain/emit/cpp/cli.py`） | C++ emitter 本体が C++ に未 transpile |

### `.json` 入力パスは既にネイティブ動作

`transpile_cli.cpp` の `.json` 分岐はシェルアウトなしで動作している。selfhost ビルドが `.py` を直接渡さず事前生成 EAST3 JSON を渡す形に統一できれば、フロントエンド側のシェルアウトは即時除去できる。

## 目的

`native/compiler/` 全 4 ファイルを削除し、selfhost バイナリがホスト Python を呼び出さずに動作できるようにする。

## 対象

- `src/runtime/cpp/native/compiler/`（削除対象）
- `src/runtime/cpp/generated/compiler/`（include 先の更新）
- selfhost ビルドパイプライン（EAST3 JSON 事前生成の統一等）
- `toolchain/emit/cpp/cli.py`（emitter の selfhost transpile 可能化）

## 非対象

- 非 C++ selfhost（Rust / C# 等）への対応（本タスクは C++ selfhost の完成に限定）
- Python AST パーサー自体の transpile（selfhost JSON 入力専用化で回避可能）

## 受け入れ基準

- `src/runtime/cpp/native/compiler/` が存在しない。
- selfhost バイナリが `python3` を呼び出さずにコンパイルを完了できる。
- selfhost diff mismatches=0。

## 子タスク

- [x] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S1] selfhost ビルドパイプラインを EAST3 JSON 入力専用に統一し、`transpile_cli.cpp` の `.py` シェルアウトパスを除去する。
- [ ] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S2] `toolchain/emit/cpp/cli.py`（emitter）を C++ に transpile 可能にし、`emit_source_typed` のシェルアウトを除去する。
- [ ] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S3] シェルアウトがゼロになったことを確認し `native/compiler/` を削除、`generated/compiler/` の include を直接 generated C++ に向け直す。

## 決定ログ

- 2026-03-18: `native/compiler/` は selfhost 未完成を示す bootstrap shim であり、移動でなく削除が正しいゴールであることを確認し起票。`.json` 入力パスは既にネイティブ動作しているため S1（フロントエンド側）は比較的コストが低い。S2（emitter の C++ transpile）が主要ブロッカー。
- 2026-03-19: S1 完了。`transpile_cli.cpp` から `.py` シェルアウトパスを除去し、`.json`/`.east` 入力専用に統一。`_run_host_python_command` / `_temp_path` / `_shell_quote` 等のシェルアウト補助関数を削除。
- 2026-03-19: S2 調査。`pytra-cli.py` に `emit_cpp_from_east` を直接 import する方式を検証したが、selfhost transpile は単一ファイル生成であり、import 先モジュール（CppEmitter 等）の C++ コードは含まれない。S2 を完了するには、emitter の全依存グラフを compile → link パイプライン（P2 で実装）で multi-module transpile し、selfhost ビルドにリンクする仕組みが必要。`backend_registry_static.cpp` の `emit_source_typed` シェルアウトは S2 完了まで残存。
