# P0 C++ iter boundary runtime contract

最終更新: 2026-04-02

## 目的

`P0-CPP-VARIANT-S10` を進める前提として、C++ backend で `ObjIterInit` / `ObjIterNext` をどう扱うかの契約を固定する。

現状は次のねじれがある。

- `src/toolchain2/compile/lower.py` は `iter.init` / `iter.next` を `ObjIterInit` / `ObjIterNext` として生成する
- `src/toolchain2/emit/cpp/emitter.py` は direct `ObjIterInit` / `ObjIterNext` を処理しない
- `src/runtime/cpp/` には `py_iter_or_raise` / `py_next_or_stop` free helper が存在しない

この状態では、`lower.py` から iter boundary を消す作業と、C++ runtime / emitter の契約整理が密結合になる。

## 進め方

1. `P0-CPP-VARIANT-S10B`
   - C++ runtime / emitter で採用する iter boundary 契約を決める
   - 候補:
     - `ObjIterInit` / `ObjIterNext` を direct emit する
     - free helper を再導入する
     - method call 契約を runtime core に戻す

2. `P0-CPP-VARIANT-S10`
   - 上記契約に沿って `lower.py` から `resolved_type="object"` Boxing と iter boundary を段階的に削る

## 完了条件

- C++ backend で `ObjIterInit` / `ObjIterNext` の受け口が定義されている
- `lower.py` の iter boundary 削除が runtime 契約未整備で止まらない
