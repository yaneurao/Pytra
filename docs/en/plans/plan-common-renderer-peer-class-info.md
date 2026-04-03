# Plan: Add receiver_storage_hint to the linker (P0-LINKER-RECEIVER-HINT)

## Background

When using transpiled stdlib types (e.g. `pytra.std.pathlib.Path`) from an entry module, the emitter needs to know whether the receiver is a ref class or a value class.

- Rust: ref class requires `child.borrow().write_text(...)`
- C++: ref class requires `child->write_text(...)`
- Go: ref class requires a pointer receiver

### Information already present in the linked EAST3

| Information | Field | Status |
|---|---|---|
| Property determination | `Attribute.attribute_access_kind: "property_getter"` | ✅ Present |
| Method return type | `Call.resolved_type` | ✅ Present |
| Method determination | `Attribute.resolved_type: "callable"` | ✅ Present |
| Receiver class_storage_hint | (none) | ❌ Missing |

**The only missing piece is `class_storage_hint`.**

## Design

### Field added by the linker

When the receiver of an `Attribute` node or `Call` node is a user-defined class type, the linker adds a `receiver_storage_hint` field:

```json
{
  "kind": "Attribute",
  "attr": "write_text",
  "value": {"kind": "Name", "id": "child", "resolved_type": "Path"},
  "resolved_type": "callable",
  "attribute_access_kind": "property_getter",
  "receiver_storage_hint": "ref"
}
```

The value is `"ref"` or `"value"`, copied directly from `ClassDef.class_storage_hint` in the peer module.

### Where the linker implements this

The linker already holds all module EAST3 in the linked bundle. It builds a map of class_name → class_storage_hint, then walks `Attribute` / `Call` nodes, looks up the receiver's `resolved_type`, and writes `receiver_storage_hint`.

```
At link time:
1. Walk all ClassDefs in all modules and build {class_name: class_storage_hint}
2. Walk all Attribute / Call nodes in all modules
3. If the receiver's resolved_type matches a class_name, attach receiver_storage_hint
```

### Changes on the emitter side

The emitter simply reads `receiver_storage_hint`:

```python
# Rust emitter's _emit_attribute
hint = node.get("receiver_storage_hint", "value")
if hint == "ref":
    return f"{receiver}.borrow().{attr}"
else:
    return f"{receiver}.{attr}"
```

No need to read peer modules. CommonRenderer / PeerClassRegistry are not required.

## Impact

- A new pass is added to the linker: class_storage_hint map construction + node walk
- All language linked EAST3 gains the `receiver_storage_hint` field
- Emitters optionally reference this field (safe to ignore if not used)
- Full parity check across all languages for fixture + sample is required

## Implementation Order

1. Add the `receiver_storage_hint` attachment pass to the linker
2. Reference `receiver_storage_hint` in the Rust emitter's `_emit_attribute` / `_emit_call`
3. Confirm that the `pathlib_extended` / `path_stringify` fixtures pass compile + run parity in Rust
4. Confirm no regressions in full fixture + sample parity
