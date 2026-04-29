# Pytra Devcontainer

この devcontainer は、ローカル環境を汚さずに Pytra の多言語 backend 作業を行うための隔離環境です。

## 含める主要ツール

- Python 3.12 系
- C/C++: gcc, g++, clang, make, CMake, Ninja
- JVM: Java 17
- Mono / C#
- PHP
- Lua 5.4 / LuaRocks
- Node.js / npm / TypeScript compiler
- Go
- Rust / Cargo
- .NET SDK 8.0
- PowerShell
- Ruby

Swift は Linux コンテナ上では重量が大きいため、この環境では optional 扱いで未導入です。

## 確認

コンテナ作成後、`.devcontainer/scripts/verify-toolchain.sh` が主要コマンドの存在を確認します。Docker がローカルにない環境では、ビルドせずにファイル定義だけを確認してください。

fresh checkout では、最初の backend build 前に次を実行して `src/runtime/east/` のローカルキャッシュを生成してください。

```bash
PYTHONPATH=src python3 tools/gen/regenerate_runtime_east.py
```
