# ランタイムの仕様について

<a href="../../en/spec/spec-runtime.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

### 0. 正本と責務境界

runtime の唯一正本（SoT）は、次の pure Python モジュール群とする。

- `src/pytra/built_in/*.py`
- `src/pytra/std/*.py`
- `src/pytra/utils/*.py`

必須ルール:

- SoT に書けるロジックは、runtime 側へ手で再実装してはならない。
- backend / emitter は、EAST で解決済みの module / symbol / signature を描画するだけとする。
- backend / emitter にライブラリ関数名、モジュール名、型名の変換テーブルや特別分岐を直書きしてはならない。
- `math`, `json`, `gif`, `png`, `Path`, `assertions`, `re`, `typing` などの知識を、変換器ソースコードへ埋めてはならない。

### 0.5 runtime 配置分類

全言語の runtime 配置は、責務で次の 4 区分に統一する。

- `src/runtime/<lang>/core/`
  - 低レベル runtime / ABI / object 表現 / GC / I/O / OS / SDK 接着など。
  - SoT の代替実装置き場ではない。
- `src/runtime/<lang>/built_in/`
  - `src/pytra/built_in/*.py` から生成した runtime。
- `src/runtime/<lang>/std/`
  - `src/pytra/std/*.py` から生成した runtime。
- `src/runtime/<lang>/utils/`
  - `src/pytra/utils/*.py` から生成した runtime。

補足:

- この分類は「生成か手書きか」ではなく「何の責務か」で切る。
- `core/` にも将来的に生成断片が入ってよい。その場合も `core/` という責務分類は維持する。
- `built_in/std/utils` は SoT 由来の生成物を置く場所であり、同等ロジックを `core/` に複製してはならない。

### 0.6 runtime ファイル命名規則

`core / built_in / std / utils` の全区分で、runtime ファイル名は次に統一する。

- 自動生成:
  - `<name>.gen.h`
  - `<name>.gen.cpp`
- 手書き拡張:
  - `<name>.ext.h`
  - `<name>.ext.cpp`

意味:

- `.gen.*`
  - SoT から機械生成したファイル。
  - 手編集禁止。
- `.ext.*`
  - ABI 接着、OS / SDK 呼び出し、`@extern` の受け皿など、言語依存の最小実装。
  - 手編集可。

必須ルール:

- 新規追加ファイルは必ず `gen/ext` 命名にする。
- suffix なしファイルは legacy とみなし、移行対象とする。新規追加は禁止。
- `*.ext.*` に SoT と同等の本体ロジックを書いてはならない。
- 生成物と手書き補完が同じモジュールに共存する場合も、basename は共有し、`.gen.*` / `.ext.*` でのみ区別する。

例:

- `src/runtime/cpp/std/math.gen.h`
- `src/runtime/cpp/std/math.ext.cpp`
- `src/runtime/cpp/utils/png.gen.cpp`
- `src/runtime/cpp/core/py_runtime.ext.h`

補足:

- `rc<list<T>>` のような backend 内部 typed handle helper を導入する場合も、配置先は `core/` とする。
- これは SoT 由来 module runtime ではなく、container / object 表現の低レベル支援層だからである。

### 0.61 include / 参照規約

- backend / build script / transpiler は、必要な runtime ファイルを suffix 付きの正規名で参照する。
- 「人が書きやすい短い unsuffixed alias」を追加してはならない。
- include / compile 時の参照先は、責務ディレクトリと `gen/ext` 命名から一意に決まるように保つ。

### 0.62 `core` と `ext` の境界

- `core/` は「低レベル runtime の責務」であって、「手書きファイル一般の置き場」ではない。
- `std/utils/built_in` のモジュール補完実装は、対応する責務ディレクトリの `.ext.*` に置く。
- `core/` に置いてよいのは、module 非依存の ABI / object / container / I/O / OS 接着だけとする。
- `rc<list<T>>` helper のような backend 内部 alias 維持層は `core/` に置いてよいが、ABI 境界ではないことを docs/spec で明記する。

誤りの例:

- `std/math` の補完実装を `core/` に置く
- `utils/png` の本体を `core/` に手書きする
- `built_in` 由来ロジックを `py_runtime` へ埋め込む

### 0.63 特殊生成スクリプト禁止

- `src/py2x.py` / 将来の統一 CLI を通さずに、特定モジュール専用の runtime 生成スクリプトを追加してはならない。
- `png.py`, `gif.py`, `json.py`, `math.py` などは、必ず正規の変換器経由で `*.gen.*` を生成する。
- runtime 生成のために、言語別の特別命名や特別テンプレートを追加してはならない。

### 0.64 `src/pytra` での `__all__` 禁止

`src/pytra/**/*.py` では `__all__` を定義してはならない。

- selfhost 実装・変換器実装の単純性を優先する。
- 公開シンボル制御は、トップレベル定義の有無で表現する。
- `built_in/std/utils` の SoT モジュールも同様に `__all__` を使わない。

### 0.65 host-only import alias 規約（`as __name`）

`import ... as __m` / `from ... import ... as __f` のように alias が `__` で始まる import は host-only import として扱う。

- host-only import は Python 実行時補助専用とする。
- 主用途は `@extern` 関数の Python フォールバック本体評価。
- トランスパイラは host-only import を EAST の `Import` / `ImportFrom` として出力しない。
- `_name` のように `_` 1 個だけの alias は host-only ではない。

### 0.66 標準ライブラリのサブモジュール実装規約

`os.path` のような標準ライブラリのサブモジュールは、独立した SoT モジュールとして扱う。

必須:

- サブモジュールは `src/pytra/std/<name>.py` に分離する。
  - 例: `os.path` -> `src/pytra/std/os_path.py`
- 親モジュールはモジュール import で参照する。
  - 例: `from pytra.std import os_path as path`
- 呼び出しは module function call として維持する。
  - 例: `path.join(...)`
- native 実装が必要な関数は、SoT 側で `@extern` 宣言し、runtime 側では対応する `.ext.*` に実体を置く。

禁止:

- サブモジュールを `object` 変数に格納する実装
- emitter / runtime でサブモジュール名に依存した特別分岐を足す実装

### 0.67 mutable 型の内部表現ポリシー

runtime / backend の内部表現は、ABI の正規形とは別に次の原則で決める。

必須ルール:

- immutable 型は value-first でよい。
  - 例: `bool`, `int`, `float`, `str`
- mutable 型は ref-first とする。
  - 例: `list`, `dict`, `set`, `bytearray`, mutable な user class
- C++ backend では、ref-first 表現として `rc<>` や同等の typed handle を使ってよい。
- ただし、これは backend 内部表現であり、ABI ではない。`@extern` 境界や言語間境界へそのまま露出してはならない。

値型縮退は、最適化の結果としてのみ許可する。

- mutable 型を「最初から値型」とみなしてはいけない。
- 値型縮退には mutation / alias / escape の解析が必要である。
- 関数をまたぐ縮退には call graph と SCC 固定点計算が必要である。
- unknown call / `Any` / `object` / `@extern` / 外部 SDK 境界をまたぐ経路は fail-closed とし、ref-first のまま残す。

補足:

- `str` のような immutable 型を値型で持つことと、`list` / `dict` を値型で持つことは同列ではない。
- `a = b` 後の破壊的更新が観測されうる型は、共有参照が正本である。
- 「一旦 ref-first にして、証明できた経路だけ stack/value へ縮退する」という順序を崩してはならない。

### 0.7 C++ runtime の運用

C++ runtime は次を正規配置とする。

- `src/runtime/cpp/core/`
- `src/runtime/cpp/built_in/`
- `src/runtime/cpp/std/`
- `src/runtime/cpp/utils/`

再生成:

- `built_in/std/utils` の SoT 由来モジュールは `--emit-runtime-cpp` で正規配置へ生成する。
- 例:
  - `python3 src/py2x.py src/pytra/built_in/type_id.py --target cpp --emit-runtime-cpp`
  - `python3 src/py2x.py src/pytra/std/math.py --target cpp --emit-runtime-cpp`
  - `python3 src/py2x.py src/pytra/utils/png.py --target cpp --emit-runtime-cpp`

最低限の検証:

- `python3 tools/check_runtime_cpp_layout.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

禁止事項:

- `*.gen.*` の手編集
- `core/` への SoT 同等ロジック再実装
- backend / emitter での module / symbol 名の直書き解決
- runtime 生成のためのモジュール専用スクリプト追加

### 0.71 多言語 runtime への適用

この分類と命名規則は C++ 専用ではなく、全言語 runtime に適用する。

- `src/runtime/<lang>/core/`
- `src/runtime/<lang>/built_in/`
- `src/runtime/<lang>/std/`
- `src/runtime/<lang>/utils/`

各言語 backend は、SoT 由来コードをそれぞれの `built_in/std/utils` に生成し、必要な最小 native 実装だけを `.ext.*` へ置く。
