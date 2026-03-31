# 計画: pytra-cli2.py から C++ 固有 import を分離 (P0-CLI2-CPP-DECOUPLE)

## 背景

`pytra-cli2.py` が top-level で `toolchain2.emit.cpp.runtime_bundle` を import しているため、Rust / Go 等の selfhost で全言語の emitter モジュールが依存グラフに入り、cargo build / go build が不要なモジュールのコンパイルエラーで失敗する。

`pytra-cli2.py` は言語非依存のパイプライン入口であるべきで、C++ 固有の import が top-level にあるのは設計違反。

## 現状

```python
# pytra-cli2.py の top-level import
from toolchain2.emit.cpp.runtime_bundle import write_helper_module_artifacts
from toolchain2.emit.cpp.runtime_bundle import write_runtime_module_artifacts
from toolchain2.emit.cpp.runtime_bundle import write_user_module_artifacts
```

使用箇所は `_emit_cpp_linked_module()` 関数のみ（264〜285行目）。この関数は `-emit` / `-build` コマンドの C++ パスでしか呼ばれない。

## 設計

### 方針

`_emit_cpp_linked_module()` を `toolchain2.emit.cpp` 側に移し、`pytra-cli2.py` からは言語非依存の API で呼び出す。

### 具体的な変更

1. `toolchain2.emit.cpp.cli` (または `toolchain2.emit.cpp.emit_linked`) に `emit_cpp_linked_module(module, output_dir)` を新設
2. `pytra-cli2.py` から `_emit_cpp_linked_module()` と `from toolchain2.emit.cpp.runtime_bundle import ...` の 3行を削除
3. `pytra-cli2.py` の `-emit` / `-build` の C++ パスで、言語ディスパッチテーブル経由で呼び出す

### 言語ディスパッチの形

```python
# pytra-cli2.py — 言語非依存
def _emit_linked_module(target: str, module: LinkedModule, output_dir: Path) -> int:
    if target == "cpp":
        from toolchain2.emit.cpp.emit_linked import emit_cpp_linked_module
        return emit_cpp_linked_module(module, output_dir)
    # 他言語は既存パス
    ...
```

ただし spec-agent.md §5 で動的 import は selfhost 対象コードでは禁止。なので:

**決定**: emitter 呼び出しのみサブプロセス化する。parse / resolve / compile / optimize / link はインメモリのまま維持。

- `pytra-cli2.py` は `-emit` / `-build` で各言語の emitter をサブプロセスで呼ぶ
- `pytra-cli.py`（旧 CLI）が既に同じ構造で selfhost も通っている
- emitter はパイプラインの最後で1回呼ばれるだけなので、サブプロセスのオーバーヘッドは無視できる
- 関数内 import は Pytra で変換できないため不可。サブプロセスが唯一の手段

## 影響範囲

- `pytra-cli2.py` の import が減る（C++ 依存が消える）
- C++ の `-build` の動作は変わらない（内部構造のリファクタのみ）
- Rust / Go の selfhost で C++ emitter がグラフに入らなくなる
- fixture + sample parity の全言語確認が必要

## 完了メモ

- `src/toolchain2/emit/cpp/cli.py` を追加し、manifest 読み込みと linked module ごとの C++ emit を C++ 側へ移した
- `src/pytra-cli2.py` は `toolchain2.emit.cpp.runtime_bundle` を import しなくなり、C++ emit は `python3 -m toolchain2.emit.cpp.cli` の subprocess に統一した
- `-build` の C++ 経路も link 結果を書き出した後に同じ subprocess emit を通す構成に変更した
- 回帰確認として `tools/unittest/tooling/test_pytra_cli2.py` を追加更新し、`pytra-cli2.py -build ... --target cpp` で sample / fixture representative の build 成功を確認した
- C++ codegen の非回帰確認として `runtime_parity_check_fast.py --targets cpp --case-root sample --east3-opt-level 2` を再実行し、`18/18 PASS` を確認した
