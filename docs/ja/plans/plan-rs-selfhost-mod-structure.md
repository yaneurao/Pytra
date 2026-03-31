# 計画: Rust selfhost の mod 構造出力 (P9-RS-MOD)

## 背景

Rust selfhost で toolchain2 (150+ モジュール) を flat `include!` で結合すると、`EmitContext` 等の top-level 型名が複数 emitter モジュール間で衝突し、`rustc` が通らない。

`include!` は「1ファイルにまとめるのが面倒なときの糊」であり、多モジュールプログラムの構成手段ではない。Rust の設計思想に沿った `mod` + `use` 構造で出力すべき。

## 現状の問題

```
// flat include! — 全モジュールが同一スコープに展開される
include!("toolchain2_emit_cs_emitter.rs");   // pub struct EmitContext { ... }
include!("toolchain2_emit_go_emitter.rs");   // pub struct EmitContext { ... }  ← 衝突
include!("toolchain2_emit_ts_emitter.rs");   // pub struct EmitContext { ... }  ← 衝突
```

## 設計

### 目標構造

```
work/selfhost/build/rs/
  src/
    main.rs                           # entry point
    lib.rs                            # mod 宣言一覧
    toolchain2_emit_cs/
      mod.rs                          # pub struct EmitContext { ... }
    toolchain2_emit_go/
      mod.rs                          # pub struct EmitContext { ... }  ← 別 mod なので衝突しない
    toolchain2_emit_ts/
      mod.rs
    toolchain2_compile/
      mod.rs
    toolchain2_link/
      mod.rs
    ...
  Cargo.toml
```

### 使い方

```rust
// main.rs or 他のモジュールから
use crate::toolchain2_emit_cs::EmitContext as CsEmitContext;
use crate::toolchain2_emit_go::EmitContext as GoEmitContext;
```

### emitter 側の変更

1. **ProgramWriter / multifile_writer** が Rust 向けに `mod` 構造を出力するモードを追加
   - 1 EAST module = 1 Rust `mod` ディレクトリ (or 1 ファイル)
   - `lib.rs` に `pub mod <module_name>;` の宣言を自動生成
   - module 間参照は `use crate::<module>::<symbol>;` を生成

2. **Rust emitter** の変更
   - `include!` 生成を `mod` + `use` 生成に置換
   - cross-module 参照で `use crate::` パスを emit
   - module-level 初期化関数の呼び出しを `main.rs` に集約

3. **`Cargo.toml` 自動生成**
   - `pytra-cli2.py -build --target rs` が `Cargo.toml` を生成
   - edition, dependencies (標準ライブラリのみ) を設定

### 他言語への影響

この問題は Rust 固有ではない。将来的に:

- **Java**: 1 module = 1 package (既に `package` 文は emit している)
- **C#**: 1 module = 1 namespace
- **Go**: 1 module = 1 package (Go は既に package 分離で動いている)

CommonRenderer / ProgramWriter に「1 module = 1 target-language namespace unit」の共通概念を持たせることで、各言語の emitter は namespace の構文だけを提供すればよくなる。ただし本タスクでは Rust のみを対象とし、共通化は別タスクとする。

## prefix hack との比較

| 観点 | prefix hack (`CsEmitContext`) | mod 構造 |
|---|---|---|
| 型名 | Python と乖離する | Python と一致 |
| selfhost の意味 | 損なう（同じコードが動かない） | 保つ |
| 名前衝突 | 手動で回避（漏れのリスク） | 言語レベルで解決 |
| `cargo build` | `include!` 前提、依存解析なし | 自然に動く |
| 将来の拡張 | 負債が増え続ける | 標準的 |

## 実施順序

1. Rust emitter の multifile_writer に mod 構造出力モードを追加
2. `lib.rs` / `Cargo.toml` の自動生成を実装
3. cross-module `use crate::` パスの emit を実装
4. `pytra-cli2.py -build --target rs` で mod 構造を使うよう切り替え
5. selfhost build (`cargo build`) が通ることを確認
6. `run_selfhost_parity.py --selfhost-lang rs` で parity 確認
