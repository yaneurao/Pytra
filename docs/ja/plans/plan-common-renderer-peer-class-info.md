# 計画: CommonRenderer に peer module クラス情報参照を追加 (P0-COMMON-PEER-CLASS)

## 背景

各言語の emitter は `_collect_module_class_info()` で自モジュールの body からクラス情報（`class_storage_hint`, method signature, field_types, property）を収集している。しかし **peer module（import 先の linked EAST3）のクラス情報を参照する仕組みがない**。

これまでは stdlib を native (skip) で持つ言語（C++, Go）では問題にならなかった。pure Python stdlib を transpile 対象にした結果、entry module から imported class（例: `pytra.std.pathlib.Path`）の method/property/ref-class 情報が emitter 側で取れず、正しいコードを生成できない問題が顕在化した。

### 影響を受ける emitter

全言語。以下の emitter が `_collect_module_class_info` を持っているが、いずれも自モジュールの body しか走査していない:

- Java, Nim, Ruby, Lua, TS, Go, Rust, CS, PHP, ...

## 設計

### linked bundle の構造（既存）

linked bundle は manifest + 各 module の linked EAST3 から構成される:

```
work/tmp/build_<case>/linked/
  manifest.json             # module 一覧
  east3/
    <entry>.east3.json      # entry module
    pytra/std/pathlib.east3.json  # peer module (class_storage_hint, methods, fields あり)
    pytra/std/json.east3.json     # peer module
    ...
```

各 peer module の linked EAST3 には `ClassDef` ノードがそのまま含まれており、`class_storage_hint`, `field_types`, method `FunctionDef` / `ClosureDef`, property 相当の定義が全て入っている。

### 追加する仕組み

CommonRenderer (または CodeEmitter 基底) に **peer class registry** を追加:

```python
@dataclass
class PeerClassInfo:
    class_storage_hint: str       # "value" | "ref"
    field_types: dict[str, str]   # field_name -> resolved_type
    method_signatures: dict[str, MethodSig]  # method_name -> (arg_types, return_type)
    properties: set[str]          # property 名の集合

class PeerClassRegistry:
    _classes: dict[str, PeerClassInfo]  # class_name -> info

    def lookup(self, class_name: str) -> PeerClassInfo | None: ...
    def is_ref_class(self, class_name: str) -> bool: ...
    def method_return_type(self, class_name: str, method: str) -> str | None: ...
```

### 初期化タイミング

emit 開始前に、linked bundle の全 peer module EAST3 を走査して `PeerClassRegistry` を構築する。これは emit の前処理であり、各モジュールの emit 中に peer module を逐次読むのではない。

```python
# emit 入口（CommonRenderer or loader.py）
registry = PeerClassRegistry()
for module in linked_modules:
    if module != entry_module:
        registry.register_from_east3(module.east_doc)
# CommonRenderer に渡す
renderer.set_peer_class_registry(registry)
```

### emitter からの参照

各 emitter の `_emit_attribute`, `_emit_call`, `_emit_assign` 等で:

```python
# 例: Attribute access
owner_type = _str(receiver, "resolved_type")
peer = ctx.peer_class_registry.lookup(owner_type)
if peer is not None and peer.is_ref_class:
    # Rc<RefCell<T>> の borrow が必要
    ...
if peer is not None and attr in peer.properties:
    # property access
    ...
```

### 既存の _collect_module_class_info との関係

- `_collect_module_class_info` は **自モジュール** のクラス情報を収集する（既存、変更なし）
- `PeerClassRegistry` は **peer module** のクラス情報を収集する（新規）
- 両方が emitter context に載り、class_name で引ける

将来的には `_collect_module_class_info` も `PeerClassRegistry` に統合してよいが、本タスクでは peer 側のみ。

## 実施順序

1. `PeerClassInfo` / `PeerClassRegistry` を `code_emitter.py` または `common_renderer.py` に追加
2. linked bundle の peer module EAST3 を走査して registry を構築するローダーを実装
3. CommonRenderer の emit 開始前に registry をセットする入口を追加
4. Rust emitter の `_emit_attribute` / `_emit_call` で registry を参照し、`pytra.std.pathlib.Path` の method/property/ref-class が正しく emit されることを確認
5. `path_stringify` / `pathlib_extended` fixture が Rust で compile + run parity PASS することを確認
6. 他言語の emitter にも順次適用（CommonRenderer 経由で自動的に使えるが、各 emitter の `_emit_attribute` 等で registry を参照するコードは個別に追加が必要）

## 影響範囲

- CommonRenderer / CodeEmitter に新しいデータ構造が追加される
- 既存の emitter の動作は変わらない（registry を参照しない限り既存パスが使われる）
- linked bundle の読み込みパスに peer module 走査が追加されるが、emit 前の1回のみ
- fixture + sample parity の全言語確認が必要
