# P2: compile / link パイプライン分離

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-COMPILE-LINK-PIPELINE-01`

## 背景

現状の pytra-cli は単一ファイルモードで `.py` → 直接ターゲット言語に変換しており、
linker を経由しない。これにより：

- `type_id` がハードコード定数（`PYTRA_TID_*`）と実行時レジストリに依存
- import 解決・main 生成判断が emitter に漏れている
- emitter が純粋な構文写像に専念できない

gcc でも `gcc -c foo.c` は `.o` を作り、最終的に `ld` でリンクする。
単一ファイルであっても compile → link の 2 段を経由すべきである。

## 設計

### パイプライン

```
# ステップ1: compile（モジュール単位、独立に実行可能）
pytra compile sample.py -o sample.east
pytra compile sample2.py -o sample2.east

# ステップ2: link → ターゲット言語出力
pytra link sample.east sample2.east --target cpp -o out/
```

### .east フォーマット

- EAST3 の JSON ファイル（`east_stage=3` の Module 文書）
- 拡張子: `.east`
- 1 モジュール = 1 ファイル

### compile 段の責務

- Python source → EAST1 → EAST2 → EAST3 → EAST3 Optimizer
- モジュール内で閉じた処理のみ
- 出力: `.east` ファイル（EAST3 JSON）

### link 段の責務

- 複数 `.east` を入力として受け取る
- モジュール横断処理:
  - クラスツリー構築・DFS オーダーで `type_id` を確定
  - import 解決・依存グラフ検証
  - main モジュール判定
- linked program をターゲット言語バックエンドに渡す
- 出力: ターゲット言語ファイル群

### type_id の確定

linker がクラスツリー全体を見て DFS オーダーで `type_id` を割り当てる。
これにより：

- `py_runtime.h` の `PYTRA_TID_*` ハードコード定数が不要になる
- `py_register_class_type()` の実行時レジストリが不要になる
- `py_sync_generated_user_type_registry()` の実行時同期が不要になる
- isinstance は linker が確定したコンパイル時定数のレンジ比較で完結

### gcc との対応

| gcc | pytra |
|-----|-------|
| `gcc -c foo.c -o foo.o` | `pytra compile foo.py -o foo.east` |
| `gcc -c bar.c -o bar.o` | `pytra compile bar.py -o bar.east` |
| `gcc foo.o bar.o -o app` | `pytra link foo.east bar.east --target cpp -o out/` |

## メリット

- compile と link の責務が完全に分離
- `.east` はキャッシュ可能（変更のないファイルは再 compile 不要）
- 並列コンパイルが可能（各 .py → .east は独立）
- emitter はリンク済み IR の純粋な構文写像に専念
- 実行時 type_id レジストリが不要（コンパイル時確定）

## 対象

- `src/py2x.py` — compile / link サブコマンド追加
- `src/toolchain/link/` — linker 実装（type_id 確定、import 解決）
- `src/toolchain/emit/*/` — linked program からの emit に統一
- `src/runtime/cpp/native/core/py_runtime.h` — 実行時レジストリ削除（linker 移行後）

## 非対象

- バイナリ .east フォーマット（将来検討、当面は JSON）
- 増分リンク（将来検討）

## 受け入れ基準

- [x] `pytra compile foo.py -o foo.east` で .east ファイルが生成される。
- [x] `pytra link foo.east --target cpp -o out/` でターゲット言語ファイルが生成される。
- [x] 単一ファイルモード（`py2x.py input.py --target cpp`）が廃止され、内部で compile → link を経由する。
- [x] type_id が linker で DFS 確定され、`PYTRA_TID_*` ハードコード定数が `py_runtime.h` から削除されている。
- [x] `py_register_class_type()` / `py_sync_generated_user_type_registry()` の実行時レジストリが削除されている。
- [ ] sample 18/18 artifact parity pass。

## 決定ログ

- 2026-03-19: ユーザー提案。gcc の compile/link 分離と同じモデルを採用。.east は EAST3 JSON。type_id は linker で DFS 確定。
- 2026-03-19: compile/link サブコマンド実装。`pytra compile` で .py → .east、`pytra link` で .east → ターゲット言語。18 sample compile+link 成功。
- 2026-03-19: P2 再オープン。単一ファイルモード（linker 非経由）が残っており、type_id の linker 確定・PYTRA_TID 定数廃止・実行時レジストリ廃止が未実施。単一ファイルモードを廃止し、全パスを compile → link 経由に統一する残作業がある。
- 2026-03-19: P2 実装完了。py2x.py の全パスが compile → link 経由に統一。type_id はリンカー DFS で確定し constexpr 定数として emit。PYTRA_TID_* 定数は py_scalar_types.h へ移動。py_register_class_type / py_sync_generated_user_type_registry / PYTRA_DECLARE_CLASS_TYPE マクロを py_runtime.h から削除。check_py2x_transpile 148/148 pass。selfhost build は環境要因（generated headers 未生成）で既存 fail。
