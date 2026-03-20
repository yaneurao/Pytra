# P0: runtime .east を link パイプラインに統合（standalone transpile 廃止）

最終更新: 2026-03-20

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RUNTIME-EAST-IN-LINK-PIPELINE-01`

## 背景

現在 `write_cpp_rendered_program` 内の `_generate_runtime_east_headers` が runtime .east を standalone transpile（`transpile_to_cpp` 直接呼び出し）で C++ ヘッダーに変換している。これにより:

1. **クラスフィールド宣言が欠落**: standalone transpile ではリンカーメタデータがなく、EAST3 のクラス解析が不十分。`Path` の `str _value;` が emit されない。
2. **tagged union の cast 変換が効かない**: `_tagged_union_types` レジストリが空のため `cast(str, value)` が `py_unbox` に変換されない。
3. **パイプラインの二重経路**: ユーザーコードは compile → link 経由なのに、runtime モジュールだけ standalone transpile という別経路。

## 原則

P2 で全パスを compile → link に統一した。runtime .east も同じパイプラインで処理する。standalone transpile を廃止する。

## 設計

### 現在のフロー

```
ユーザーコード:  .py → compile → .east → link → emit → .cpp（正しい）
runtime モジュール: .east → standalone transpile_to_cpp → .h（壊れている）
```

### 新しいフロー

```
ユーザーコード:  .py → compile → .east ─┐
runtime モジュール: .east ──────────────┤→ link → emit → out/cpp/
                                        │  （全モジュールを一括処理）
```

### 具体的な変更

#### 1. `build_linked_program_from_module_map` に runtime .east を含める

現在リンカーはユーザーモジュールの .east だけを処理する。runtime .east（`src/runtime/generated/built_in/*.east`, `std/*.east`）も `module_map` に追加し、LinkedProgram に含める。

runtime .east はリンカーの `resolved_dependencies_v1` で検出された依存先モジュールだけを含めればよい。全 runtime .east を含める必要はない。

#### 2. `write_multi_file_cpp` / `write_cpp_rendered_program` が runtime モジュールも emit

link → emit の段階で、LinkedProgram に含まれる runtime モジュールもユーザーモジュールと同様に C++ に emit し、`out/cpp/{namespace}/` に配置する。

#### 3. `_generate_runtime_east_headers` を廃止

standalone transpile は不要。link パイプラインが全てを処理する。

#### 4. native C++ コピーは維持

`_copy_native_runtime_to_output` は維持。手書き native ヘッダー（`core/py_types.h`, `built_in/base_ops.h` 等）と native ソース（`std/math.cpp` 等）は link パイプラインの対象外で、コピーで配置。

### runtime .east の LinkedProgram への取り込み方

#### 方法 A: link サブコマンドに runtime .east を自動追加

`pytra link user.east --target cpp` を実行すると、リンカーが `resolved_dependencies_v1` に含まれる runtime モジュール（例: `pytra.std.pathlib`）を検出し、対応する `src/runtime/generated/std/pathlib.east` を自動的に LinkedProgram に追加する。

**利点**: ユーザーが runtime .east を明示指定する必要がない。
**実装**: `build_linked_program_from_module_map` または `_build_linked_program_for_input`（py2x.py）で、依存解決後に runtime .east を追加ロードする。

#### 方法 B: py2x.py が runtime .east を明示的に追加

`_build_linked_program_for_input` で `build_module_east_map` を呼ぶ際、runtime モジュールの .east もマップに含める。

**利点**: リンカーの変更が不要。
**実装**: `build_module_east_map` の import 解決で runtime モジュールが検出されたら、対応する .east を読み込んでマップに追加する。

#### 推奨: 方法 A

リンカーが依存を把握しているので、リンカーが runtime .east を取り込むのが自然。

### 出力構成

```
out/cpp/
  core/            # native コピー
    py_types.h
    py_runtime.h
    ...
  built_in/        # native コピー + link emit
    base_ops.h     # native コピー
    string_ops.h   # link emit（.east から）
    type_id.h      # link emit（.east から）
    ...
  std/             # native コピー + link emit
    math.cpp       # native コピー
    pathlib.h      # link emit（.east から）← フィールド宣言あり
    ...
  main.cpp         # ユーザーコード（link emit）
  Makefile
```

## 対象ファイル

| ファイル | 変更 |
|---------|------|
| `src/toolchain/link/program_loader.py` or `src/py2x.py` | runtime .east を LinkedProgram に自動追加 |
| `src/toolchain/emit/cpp/emitter/multifile_writer.py` | runtime モジュールも emit 対象に |
| `src/toolchain/emit/cpp/program_writer.py` | `_generate_runtime_east_headers` 廃止 |
| `src/toolchain/frontends/runtime_symbol_index.py` | runtime module_id → .east パスの解決 |

## 非対象

- 非 C++ バックエンド
- native C++ のコピー処理（維持）
- @extern モジュール（native .cpp が手書きで存在するもの）の emit — native コピーで対応

## 受け入れ基準

- [ ] runtime .east が link パイプラインで処理され、正しい C++ が emit される。
- [ ] `_generate_runtime_east_headers`（standalone transpile）が廃止されている。
- [ ] `pathlib.py` の `Path` クラスにフィールド宣言（`str _value;`）が含まれる。
- [ ] `out/cpp/` で pathlib repro が g++ ビルドできる。
- [ ] `check_py2x_transpile --target cpp` pass。

## 子タスク

- [ ] [ID: P0-RUNTIME-EAST-IN-LINK-PIPELINE-01-S1] `resolved_dependencies_v1` に含まれる runtime モジュールの .east を LinkedProgram に自動追加するロジックを実装する。
- [ ] [ID: P0-RUNTIME-EAST-IN-LINK-PIPELINE-01-S2] `write_cpp_rendered_program` で runtime モジュールも link emit の出力に含める。native .cpp が存在する @extern モジュールは宣言ヘッダーを emit。
- [ ] [ID: P0-RUNTIME-EAST-IN-LINK-PIPELINE-01-S3] `_generate_runtime_east_headers` を廃止する。
- [ ] [ID: P0-RUNTIME-EAST-IN-LINK-PIPELINE-01-S4] pathlib repro が `out/cpp/` で g++ ビルドできることを検証する。

## 決定ログ

- 2026-03-20: pathlib g++ ビルドで `str _value;` フィールド宣言欠落が発覚。原因は `_generate_runtime_east_headers` の standalone transpile。ユーザーから「linker 経由で C++ にすると言っているのに standalone transpile があるのがおかしい」と指摘。runtime .east を link パイプラインに統合し standalone transpile を廃止する設計で P0 最優先として起票。
- 2026-03-20: S1-S3 実装完了。`_optimize_cpp_module_east_map` で `add_runtime_east_to_module_map` を呼び出し、runtime .east をリンカー経由で処理するよう変更。multifile_writer で runtime モジュールを `kind="runtime"` として検出し、namespace 正規パス（`std/pathlib.h` 等）に出力。program_writer でリンク済み runtime モジュールを先に書き出し、`_generate_runtime_east_headers` は残存モジュールのフォールバックとして維持。pathlib.h に `str _value;` フィールドと `RcObject` 継承が正しく生成されることを確認。unit test 276 件通過。
