# ランタイムの仕様について

<a href="../../en/spec/spec-runtime.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

### 0. C++ runtime API 正本カタログ（P2-S1-01）

`P2-RUNTIME-PARITY-CPP-01` の Wave 設計では、ここを「他言語 runtime 同等化」の基準 API とする。

- 正本配置:
  - core helper: `src/runtime/cpp/core/built_in/py_runtime.h`
  - 生成 runtime: `src/runtime/cpp/gen/{std,utils}/*.h`
  - `src/runtime/cpp/pytra/` 互換 forwarder 層は廃止済み（新規追加禁止）
- 受理ルール:
  - API 名と引数契約は C++ を正本とする。
  - 他言語は同名 API か adapter 経由で同等契約を満たす。
  - `Must` は parity 優先実装、`Should` は段階導入対象。

| モジュール | C++ API（基準） | 契約サマリ | 優先度 |
| --- | --- | --- | --- |
| `built_in/core` | `py_truthy`, `py_len`, `py_to<T>`, `py_to_int64`, `py_to_float64`, `py_to_bool`, `py_to_string`, `py_os_path_*`, `py_glob_glob`, `py_at`, `py_slice`, `py_dict_get(_default)` | 生成コードが直接利用する最小演算/変換/コンテナ/パス操作。型不一致時は fail-closed（例外/既定値契約を API ごとに維持）。 | Must |
| `pytra::std::math` | `pi`, `e`, `sqrt`, `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `fabs`, `floor`, `ceil`, `pow` | `float64` 入出力を基準に数値演算契約を統一。 | Must |
| `pytra::std::time` | `perf_counter()` | 単調増加の高分解能時刻を `float64` 秒で返す。 | Must |
| `pytra::std::pathlib::Path` | `__truediv__`, `parent`, `parents`, `name`, `suffix`, `stem`, `resolve`, `exists`, `mkdir`, `read_text`, `write_text`, `glob`, `cwd` | `Path` 型の最小操作集合。`read_text/write_text` は UTF-8 文字列経路を基準。 | Must |
| `pytra::std::json` | `loads`, `dumps`（補助: `_dump_json_*`, `_escape_str`） | JSON 文字列との相互変換。公開契約は `loads/dumps` を基準。 | Must |
| `pytra::utils::png` | `write_rgb_png(path, width, height, pixels)` | RGB バイト列を PNG ファイルへ保存。 | Must |
| `pytra::utils::gif` | `grayscale_palette()`, `save_gif(path, width, height, frames, palette, delay_cs, loop)` | グレースケール palette 生成と GIF 保存。 | Must |
| `pytra::std::timeit` | `default_timer()` | 計測補助 API。`perf_counter` と同系統契約。 | Should |
| `pytra::std::random` | `random`, `seed`, `randrange`, `randint`, `uniform`, `choice` | 乱数 API の最小互換。結果分布契約を優先し、完全同値までは要求しない。 | Should |

注記:
- `pytra::std::json` / `pytra::utils::{png,gif}` は内部補助関数を含むが、多言語同等化で必須なのは公開 API。
- `Path` は現状 `gen/std/pathlib.h` の宣言が薄く、`.cpp` 側 struct 実体が実効 API になっている。Wave1 で宣言/実体の整合も合わせて正規化対象とする。

### 0.5 SoT / pytra-core / pytra-gen の責務境界（P2-RUNTIME-PARITY-CPP-02-S1-02）

この節は全言語共通の必須ルールであり、例外は allowlist と監査ログで明示した場合のみ許可する。

- SoT（唯一正本）
  - `src/pytra/std/*.py`
  - `src/pytra/utils/*.py`
- runtime 配置（全言語共通）
  - `src/runtime/<lang>/pytra-core/`: 言語依存の最小基盤（I/O, FS, 時刻, VM/SDK 接着など）
  - `src/runtime/<lang>/pytra-gen/`: SoT 由来の生成物のみ（手編集禁止）
  - C++ は新レイアウトとして `src/runtime/cpp/core/` / `src/runtime/cpp/gen/` を使用する（`pytra-core/pytra-gen` の C++ 側旧名は廃止）。

必須:

- SoT で表現可能な API は `pytra-gen` に配置し、`pytra-core` に同等ロジックを手書きしない。
- `pytra-gen` 生成物は機械的素通し命名を維持する（例: `png.py -> png.<ext>`, `gif.py -> gif.<ext>`）。
- `pytra-gen` 生成物に `source:` / `generated-by:` marker を残し、生成元追跡を必須化する。
- runtime/stdlib 呼び出し解決は EAST3（`runtime_call` / `resolved_runtime_call` / `resolved_runtime_source`）を正本とし、backend/emitter は解決済み情報の描画に限定する。

禁止:

- `pytra-core` への SoT 同等機能の再実装（`json/assertions/re/typing/png/gif` 等）。
- SoT 由来ファイルの特別命名（例: `GifHelper`, `PngHelper`）や runtime への埋め込み。
- emitter でのライブラリ関数名直書き分岐（`callee_name == "..."`, `attr_name == "..."`, 固定 dispatch table）。

監査/CI:

- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/audit_image_runtime_sot.py --fail-on-core-mix --fail-on-gen-markers`
- `python3 tools/check_emitter_runtimecall_guardrails.py`
- `python3 tools/check_emitter_forbidden_runtime_symbols.py`

### 0.6 `std/utils` モジュール分類表（P2-RUNTIME-PARITY-CPP-02-S1-03）

以下は `src/pytra/std/*.py` / `src/pytra/utils/*.py` を起点にした分類で、全言語共通で適用する。

| モジュール | 区分 | 配置ルール | 備考 |
| --- | --- | --- | --- |
| `argparse`, `dataclasses`, `enum`, `glob`, `json`, `math`, `os`, `pathlib`, `random`, `re`, `sys`, `time`, `timeit`, `traceback`, `typing` | 生成必須 | `src/runtime/<lang>/pytra-gen/std/<mod>.<ext>` | SoT 由来。`pytra-core` へ同等ロジックを置かない。 |
| `assertions`, `gif`, `png` | 生成必須 | `src/runtime/<lang>/pytra-gen/utils/<mod>.<ext>` | 画像/検証ロジックは必ず生成物を使う。 |
| `dataclasses_impl`, `math_impl`, `time_impl` | core許可（impl境界） | `src/runtime/<lang>/pytra-core/std/*-impl.<ext>` | 言語/SDK 依存 primitive のみ許可。公開 API 本体は `pytra-gen` 側。 |

補足:

- `*_impl` は「ネイティブ依存の最小 primitive 層」であり、SoT 本体の代替実装ではない。
- `pytra-core` 側に同名 API の本体を増やす場合は、`S2-03`（棚卸し+移管計画）で明示審査する。

### 0.65 手書き実装ファイルの命名規約（衝突回避）

`<mod>.cpp` を生成物として維持するモジュールでは、手書き実装との衝突を防ぐため以下を必須とする。

- 生成専用:
  - `<mod>.h`
  - `<mod>.cpp`
- 手書き専用:
  - `<mod>-manual.h`
  - `<mod>-manual.cpp`

運用ルール:

- 生成器が出力する `<mod>.cpp` は手編集禁止。
- 手書き実装が必要な場合は必ず `-manual` 側へ実装し、生成側から委譲する。
- 既存の `*-impl` は移行中の暫定互換として残存しうるが、新規追加は `-manual` を使う。
- 将来の統一命名は `-manual` を正とする。

### 0.66 `src/pytra` での `__all__` 禁止ルール

`src/pytra/**/*.py` では `__all__` を定義してはならない。

- selfhost 実装・変換器実装の単純性を優先し、公開シンボル制御は `__all__` ではなくトップレベル定義の有無で表現する。
- runtime SoT モジュール（`src/pytra/std`, `src/pytra/utils`, `src/pytra/built_in`）も同様に `__all__` を使わない。
- 既存モジュールに `__all__` が残っている場合は削除し、生成物側で必要な補助状態（例: `__all__` 変数生成）を持ち込まない。

### 0.67 host-only import alias 規約（`as __name`）

`import ... as __m` / `from ... import ... as __f` のように alias が `__` で始まる import は、host-only import として扱う。

- host-only import は Python 実行時補助（主に `@extern` 関数のフォールバック本体評価）専用とする。
- トランスパイラは host-only import を EAST の `Import` / `ImportFrom` として出力しない。
- alias が `_name`（`_` 1個）で始まるだけの import は host-only ではない。通常 import として扱う。
- `src/pytra/std/*.py` でホスト標準ライブラリに委譲する場合は `as __name` を使う。

### 0.68 標準ライブラリのサブモジュール実装規約（`os.path` など）

`os.path` のような標準ライブラリのサブモジュールは、`object` 属性として扱わず、SoT 上の独立モジュールとして実装する。

必須:

- サブモジュールは `src/pytra/std/<name>.py` に分離する（例: `os.path` は `src/pytra/std/os_path.py`）。
- 親モジュールはモジュール import で参照する（例: `from pytra.std import os_path as path`）。
- 呼び出しは「モジュール関数呼び出し」として表現する（例: `path.join(...)`）。backend は解決済み module/symbol を描画するだけとする。
- ネイティブ実装が必要な関数はサブモジュール側で `@extern` 宣言し、C++ では `*-manual.cpp` に実体を置く。

禁止:

- `path: object = extern(__os.path)` のような「サブモジュールを object 変数へ格納する」実装。
- emitter/runtime でサブモジュール名に依存した特別分岐を追加する実装。

### 0.7 C++ runtime（core/gen）運用手順

再生成:

- SoT 由来モジュールは `--emit-runtime-cpp` で `src/runtime/cpp/gen/` に直接再生成する。
- 例:
  - `python3 src/py2x.py src/pytra/std/math.py --target cpp --emit-runtime-cpp`
  - `python3 src/py2x.py src/pytra/utils/png.py --target cpp --emit-runtime-cpp`
  - `python3 src/py2x.py src/pytra/built_in/type_id.py --target cpp --emit-runtime-cpp`

検証（最低限）:

- `python3 tools/check_runtime_cpp_layout.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/check_runtime_core_gen_markers.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

禁止事項:

- `src/runtime/cpp/gen/` の手編集
- `src/runtime/cpp/core/` への SoT 同等ロジック再実装
- `src/runtime/cpp/pytra/` 互換 forwarder の再導入


### 1. 生成物と手書き実装の責務分離を明文化する

- 自動生成:
  - `runtime/cpp/gen/std/<mod>.h`
  - `runtime/cpp/gen/std/<mod>.cpp`
  - `runtime/cpp/gen/utils/<mod>.h`
  - `runtime/cpp/gen/utils/<mod>.cpp`
  - 例: `runtime/cpp/gen/std/json.h/.cpp`, `runtime/cpp/gen/std/typing.h/.cpp`,
    `runtime/cpp/gen/utils/assertions.h/.cpp`
  - `runtime/cpp/gen/std/math.h` / `math.cpp` は `src/pytra/std/math.py` を `src/py2x.py --target cpp` で解釈した結果（関数シグネチャ）から生成する。
- 手書き許可:
  - `runtime/cpp/core/std/<mod>-impl.cpp`
  - `runtime/cpp/core/utils/<mod>-impl.cpp`
- ルール:
  - `<mod>.h/.cpp` は常に再生成対象（手編集禁止）。
  - `*-impl.cpp` は手編集可能（再生成対象外）。
  - `<mod>.cpp` から `*-impl.cpp` の関数へ委譲する。
  - 生成器は `src/py2x.py --target cpp` のみを正とし、特定モジュール専用の生成スクリプトは追加しない。
  - 既定出力先への生成は `py2x.py --target cpp --emit-runtime-cpp` を使う。

### 2. include規約を固定する

- 生成コード側で import に対応して出力する include は次で固定する。
  - `from pytra.std.glob import glob` -> `#include "pytra/std/glob.h"`
  - `from pytra.utils.gif import save_gif` -> `#include "pytra/utils/gif.h"`
- トランスパイラが include パスを 1 方式に固定し、旧配置との混在を禁止する。
- ルール追加:
  - Python の import 名と C++ include パスは 1 対 1 対応にする。
  - 例: `import pytra.std.math` -> `#include "pytra/std/math.h"`。
  - 例: `import pytra.utils.png` -> `#include "pytra/utils/png.h"`。
  - コンパイル時は `src/runtime/cpp` を include ルート（`-I`）として渡す。
  - 組み込み基盤ヘッダは `runtime/cpp/core/built_in/py_runtime.h` を正本とする。
  - `runtime/cpp/core/built_in/*.h` の相互 include は同一ディレクトリ相対（例: `#include "str.h"`）で記述する。

#### 2.0 built_in ヘッダの guard ルール

- `runtime/cpp/core/built_in/*.h` の include guard は、`runtime/cpp/core/` 以降の相対パスから生成する。
  - 変換規則: `/` と `.` と `-` を `_` に置換し、英大文字化し、先頭に `PYTRA_` を付ける。
  - 例: `runtime/cpp/core/built_in/list.h` -> `PYTRA_BUILT_IN_LIST_H`
  - 例: `runtime/cpp/core/built_in/py_runtime.h` -> `PYTRA_BUILT_IN_PY_RUNTIME_H`

#### 2.1 モジュール名変換ルール（自作モジュール向け）

基本ルール:
- `pytra.std.<mod>` は `pytra::std::<mod>` に対応する。
- `pytra.utils.<mod>` は `pytra::utils::<mod>` に対応する。
- include パスは `.` を `/` に変換して `.h` を付ける。
- 末尾が `_impl` のモジュールだけは、include パスで `_impl -> -impl` に写像する。
- namespace は `_impl` のまま維持する（`-impl` にはしない）。
- `.h` 出力は「モジュール単位」で作成される。
  - 生成先: `runtime/cpp/gen/std/<mod>.h` または `runtime/cpp/gen/utils/<mod>.h`
  - モジュールのトップレベル関数は宣言になる（定義は `.cpp`）
  - モジュールのトップレベル定数/変数は `extern` 宣言になる（実体は `.cpp`）

例1: 標準モジュール（通常）

```python
import pytra.std.time as t

def now() -> float:
    return t.perf_counter()
```

```cpp
#include "pytra/std/time.h"

double now() {
    return pytra::std::time::perf_counter();
}
```

`pytra.std.time` 側の `.h` は次の形になる:

```cpp
// runtime/cpp/gen/std/time.h
namespace pytra::std::time {
double perf_counter();
}  // namespace pytra::std::time
```

例2: ランタイムモジュール（通常）

```python
import pytra.utils.png as png

def save(path: str, w: int, h: int, pixels: bytes) -> None:
    png.write_rgb_png(path, w, h, pixels)
```

```cpp
#include "pytra/utils/png.h"

void save(const str& path, int64 w, int64 h, const bytes& pixels) {
    pytra::utils::png::write_rgb_png(path, w, h, pixels);
}
```

例3: `_impl` 付きモジュール（特別規則）

```python
import pytra.std.math_impl as _m

def root(x: float) -> float:
    return _m.sqrt(x)
```

```cpp
#include "pytra/std/math-impl.h"  // include は -impl

float64 root(float64 x) {
    return pytra::std::math_impl::sqrt(x);  // namespace は _impl
}
```

例4: ユーザー定義 native モジュールを追加する場合

```python
import pytra.std.foo_impl as _f

def f(x: float) -> float:
    return _f.calc(x)
```

```cpp
#include "pytra/std/foo-impl.h"

float64 f(float64 x) {
    return pytra::std::foo_impl::calc(x);
}
```

定数を持つモジュールの `.h` は `extern` 宣言になる:

```cpp
// runtime/cpp/gen/std/math.h
namespace pytra::std::math {
extern double pi;
extern double e;
double sqrt(double x);
}  // namespace pytra::std::math
```

#### 2.2 Python入力から `.h/.cpp` が生成される流れ（定数を含む）

次の Python を入力として `py2x.py --target cpp` を実行すると、`.h` と `.cpp` の両方が生成される。

```python
# src/pytra/std/math.py
import pytra.std.math_impl as _m

pi: float = _m.pi
e: float = _m.e

def sqrt(x: float) -> float:
    return _m.sqrt(x)
```

生成コマンド（例）:

```bash
# 既定パスへ直接生成
python3 src/py2x.py src/pytra/std/math.py --target cpp --emit-runtime-cpp

# 任意パスへ生成
python3 src/py2x.py src/pytra/std/math.py --target cpp \
  -o /tmp/math.cpp \
  --header-output /tmp/math.h \
  --top-namespace pytra::std::math
```

生成 `.h` の例（定数宣言 + 関数宣言）:

```cpp
namespace pytra::std::math {

extern double pi;
extern double e;

double sqrt(double x);

}  // namespace pytra::std::math
```

生成 `.cpp` の例（定数定義 + 関数定義）:

```cpp
#include "pytra/std/math-impl.h"

namespace pytra::std::math {

float64 pi = py_to_float64(pytra::std::math_impl::pi);
float64 e = py_to_float64(pytra::std::math_impl::e);

float64 sqrt(float64 x) {
    return py_to_float64(pytra::std::math_impl::sqrt(x));
}

}  // namespace pytra::std::math
```

要点:
- Python のモジュール変数代入（`pi = _m.pi`）は、C++ 側では
  - `.h`: `extern` 宣言
  - `.cpp`: 実体定義
  として出力される。
- import 先が `_impl` の場合、include は `-impl.h`、namespace は `_impl` のままになる。

### 3. 自作モジュール import の生成仕様を追加する

- `import mylib` / `from mylib import f` の場合:
  - `mylib.py` -> `mylib.h` / `mylib.cpp` を生成する。
- 依存解決:
  - import グラフを先に構築し、トポロジカル順で生成する。
  - 循環 import はエラー（`input_invalid`）とする。
- 名前衝突:
  - `pytra.*` と同名のユーザーモジュールは禁止（`input_invalid`）。

### 4. `*-impl.cpp` のABI境界を固定する

- `*-impl.cpp` に置く関数は C++ 依存の最小 primitive だけに限定する。
  - 例: filesystem, regex, clock, process, OS API
- それ以外のロジック（整形・変換・検証）は Python 側 (`src/pytra/utils/*.py`) に残す。
- これにより、言語間差異を `*-impl` 層へ閉じ込める。

### 5. 生成テンプレートの最小ルール

- 生成 `<mod>.h`:
  - 公開 API 宣言のみ
  - include guard / namespace 定義
  - `py2x.py --target cpp --header-output` で EAST から生成する（手編集しない）
- 生成 `<mod>.cpp`:
  - `#include "<mod>.h"`
  - 必要なら `#include "<mod>-impl.cpp"` は行わず、関数宣言経由でリンク解決する
  - 変換された Python ロジック本体 + `*-impl` 呼び出し
  - `py2x.py --target cpp -o <mod>.cpp` で生成する（手編集しない）
  - `pytra.utils.png` / `pytra.utils.gif` は bridge 方式:
    - 変換本体を `namespace ...::generated` に出力
    - 公開 API (`write_rgb_png`, `save_gif`, `grayscale_palette`) は bridge 関数で型変換して公開

- 予約命名:
  - Python モジュール名の末尾 `_impl` は C++ ヘッダパスで `-impl` に写像する。
  - 例: `import pytra.std.math_impl` -> `#include "pytra/std/math-impl.h"`

### 6. テスト要件を仕様に含める

- 各モジュールで最低限次を満たすこと:
  1. Python実行結果と C++ 実行結果が一致する
  2. `runtime/cpp/gen/std` と `runtime/cpp/gen/utils` に対応する import 形式（`import` / `from ... import ...`）の両方が通る
  3. 生成物を削除して再生成しても差分が安定する（再現可能）

### 7. 将来の多言語展開を見据えた命名

- C++ 固有名（`-impl.cpp`）の概念は維持しつつ、他言語では同等の役割名に置換する。
  - 例: `-impl.cs`, `-impl.rs` など
- 仕様文書では「ネイティブ実装層（impl層）」として抽象名で定義する。

### 8. 現行配置の固定

- C++ ランタイム実体は `runtime/cpp/gen/std/*` と `runtime/cpp/gen/utils/*` を正とする。
- include は現時点で上記パスを直接参照する方式に固定する。
- 将来レイアウト変更を行う場合は、本仕様を先に更新してから実装変更する。

### 9. 命名方針

- ライブラリ階層は次の2系統に統一する。
  - `pytra.std`: Python 標準ライブラリ代替
  - `pytra.utils`: Pytra 固有ランタイム補助
- `utils` のような汎用名は使わず、責務が読める名前を優先する。

### 10. `pytra.*` モジュール変換方針（無視禁止）

- `pytra.std.*` / `pytra.utils.*` は通常の Python モジュールとして扱う。
  - `import` / モジュール変数代入 / 関数本体を「フォルダ名だけで」無視してはならない。
  - 例: `pi = _m.pi`、`def sqrt(...): return _m.sqrt(...)` は意味を持つ記述として扱う。
- ネイティブ実装への差し替えは、明示的境界でのみ許可する。
  - 生成物（例: `runtime/cpp/gen/std/math.h/.cpp`）から手書き実装（例: `py_math.h/.cpp` または `*-impl.cpp`）へ委譲する。
  - 暗黙ルール（「このフォルダ配下は関数宣言以外を無視」など）は禁止する。
- 公式モジュールとユーザー自作モジュールには同じ変換ルールを適用する。
  - 公式のみ特別扱いして、ユーザー側で同等構成を再現不能にしてはならない。

### 11. C++ 側の定数/関数の受け皿

- C++ 生成側では、Python 側モジュール定義を保持したまま、必要に応じてネイティブ関数へマップする。
- 例（`pytra.std.math`）:
  - `pi = _m.pi` は
    - `.h`: `extern double pi;`
    - `.cpp`: `float64 pi = py_to_float64(pytra::std::math_impl::pi);`
    のように宣言/定義へ分離して受ける。
  - `return _m.sqrt(x)` は `pytra::std::math_impl::sqrt(x)` 呼び出しで受ける。
- 上記マップ先（`pytra::std::<name>_impl::*`）は手書き実装として事前に提供し、生成コードはそれを参照する。

### 12. `Any` / `object` 表現方針（C++）

- `Any` は C++ では `object`（`rc<PyObj>`）として表現する。
- `None` は `object{}`（null ハンドル）として表現する。
- boxing/unboxing は `make_object(...)` / `obj_to_*` / `py_to_*` を使用する。
- EAST 側の注釈正規化（`any` / `object` は `Any` 同義）から C++ 実装へ落とす際の具体化として、この方針を適用する。
- EAST 側の定義は [EAST仕様（実装準拠）](./spec-east.md) を参照する。
