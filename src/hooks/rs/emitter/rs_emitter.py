"""EAST -> Rust transpiler."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.rs.hooks.rs_hooks import build_rs_hooks
from pytra.compiler.east_parts.code_emitter import CodeEmitter


RUST_RUNTIME_SUPPORT = """use std::fs;
use std::io::Write;
use std::sync::Once;
use std::time::Instant;

fn py_perf_counter() -> f64 {
    static INIT: Once = Once::new();
    static mut START: Option<Instant> = None;
    INIT.call_once(|| unsafe {
        START = Some(Instant::now());
    });
    unsafe {
        START
            .as_ref()
            .expect("perf counter start must be initialized")
            .elapsed()
            .as_secs_f64()
    }
}

fn py_isdigit(v: &str) -> bool {
    if v.is_empty() {
        return false;
    }
    v.chars().all(|c| c.is_ascii_digit())
}

fn py_isalpha(v: &str) -> bool {
    if v.is_empty() {
        return false;
    }
    v.chars().all(|c| c.is_ascii_alphabetic())
}

fn py_str_at(s: &str, index: i64) -> String {
    let n = if s.is_ascii() { s.len() as i64 } else { s.chars().count() as i64 };
    let mut idx = index;
    if idx < 0 {
        idx += n;
    }
    if idx < 0 || idx >= n {
        return String::new();
    }
    if s.is_ascii() {
        let b = s.as_bytes()[idx as usize];
        return (b as char).to_string();
    }
    s.chars().nth(idx as usize).map(|c| c.to_string()).unwrap_or_default()
}

fn py_slice_str(s: &str, start: Option<i64>, end: Option<i64>) -> String {
    let n = if s.is_ascii() { s.len() as i64 } else { s.chars().count() as i64 };
    let mut i = start.unwrap_or(0);
    let mut j = end.unwrap_or(n);
    if i < 0 {
        i += n;
    }
    if j < 0 {
        j += n;
    }
    if i < 0 {
        i = 0;
    }
    if j < 0 {
        j = 0;
    }
    if i > n {
        i = n;
    }
    if j > n {
        j = n;
    }
    if j < i {
        j = i;
    }
    if s.is_ascii() {
        return s[(i as usize)..(j as usize)].to_string();
    }
    let start_b = if i == 0 {
        0
    } else {
        s.char_indices()
            .nth(i as usize)
            .map(|(b, _)| b)
            .unwrap_or(s.len())
    };
    let end_b = if j == n {
        s.len()
    } else {
        s.char_indices()
            .nth(j as usize)
            .map(|(b, _)| b)
            .unwrap_or(s.len())
    };
    s[start_b..end_b].to_string()
}

fn py_grayscale_palette() -> Vec<u8> {
    let mut p = Vec::<u8>::with_capacity(256 * 3);
    let mut i: u16 = 0;
    while i < 256 {
        let v = i as u8;
        p.push(v);
        p.push(v);
        p.push(v);
        i += 1;
    }
    p
}

fn py_png_crc32(data: &[u8]) -> u32 {
    let mut crc: u32 = 0xFFFF_FFFF;
    for &b in data {
        crc ^= b as u32;
        for _ in 0..8 {
            if (crc & 1) != 0 {
                crc = (crc >> 1) ^ 0xEDB8_8320;
            } else {
                crc >>= 1;
            }
        }
    }
    !crc
}

fn py_png_adler32(data: &[u8]) -> u32 {
    const MOD: u32 = 65521;
    let mut s1: u32 = 1;
    let mut s2: u32 = 0;
    for &b in data {
        s1 = (s1 + b as u32) % MOD;
        s2 = (s2 + s1) % MOD;
    }
    (s2 << 16) | s1
}

fn py_png_chunk(kind: &[u8; 4], data: &[u8]) -> Vec<u8> {
    let mut out = Vec::<u8>::with_capacity(12 + data.len());
    out.extend_from_slice(&(data.len() as u32).to_be_bytes());
    out.extend_from_slice(kind);
    out.extend_from_slice(data);
    let mut crc_input = Vec::<u8>::with_capacity(4 + data.len());
    crc_input.extend_from_slice(kind);
    crc_input.extend_from_slice(data);
    out.extend_from_slice(&py_png_crc32(&crc_input).to_be_bytes());
    out
}

fn py_zlib_store_compress(raw: &[u8]) -> Vec<u8> {
    let mut out = Vec::<u8>::with_capacity(raw.len() + 64);
    out.push(0x78);
    out.push(0x01);

    let mut pos: usize = 0;
    while pos < raw.len() {
        let remain = raw.len() - pos;
        let block_len = if remain > 65_535 { 65_535 } else { remain };
        let final_block = pos + block_len >= raw.len();
        out.push(if final_block { 0x01 } else { 0x00 });
        let len = block_len as u16;
        let nlen = !len;
        out.extend_from_slice(&len.to_le_bytes());
        out.extend_from_slice(&nlen.to_le_bytes());
        out.extend_from_slice(&raw[pos..(pos + block_len)]);
        pos += block_len;
    }
    out.extend_from_slice(&py_png_adler32(raw).to_be_bytes());
    out
}

fn py_write_rgb_png(path: &str, width: i64, height: i64, pixels: &[u8]) {
    if width <= 0 || height <= 0 {
        panic!("invalid image size");
    }
    let w = width as usize;
    let h = height as usize;
    let expected = w * h * 3;
    if pixels.len() != expected {
        panic!("pixels length mismatch: got={} expected={}", pixels.len(), expected);
    }

    let row_bytes = w * 3;
    let mut scanlines = Vec::<u8>::with_capacity(h * (row_bytes + 1));
    for y in 0..h {
        scanlines.push(0);
        let start = y * row_bytes;
        scanlines.extend_from_slice(&pixels[start..(start + row_bytes)]);
    }

    let mut ihdr = Vec::<u8>::with_capacity(13);
    ihdr.extend_from_slice(&(width as u32).to_be_bytes());
    ihdr.extend_from_slice(&(height as u32).to_be_bytes());
    ihdr.push(8);
    ihdr.push(2);
    ihdr.push(0);
    ihdr.push(0);
    ihdr.push(0);

    let idat = py_zlib_store_compress(&scanlines);
    let mut png = Vec::<u8>::new();
    png.extend_from_slice(&[0x89, b'P', b'N', b'G', 0x0D, 0x0A, 0x1A, 0x0A]);
    png.extend_from_slice(&py_png_chunk(b"IHDR", &ihdr));
    png.extend_from_slice(&py_png_chunk(b"IDAT", &idat));
    png.extend_from_slice(&py_png_chunk(b"IEND", &[]));

    let parent = std::path::Path::new(path).parent();
    if let Some(dir) = parent {
        let _ = fs::create_dir_all(dir);
    }
    let mut f = fs::File::create(path).expect("create png file failed");
    f.write_all(&png).expect("write png file failed");
}

fn py_gif_lzw_encode(data: &[u8], min_code_size: u8) -> Vec<u8> {
    if data.is_empty() {
        return Vec::new();
    }
    let clear_code: u16 = 1u16 << min_code_size;
    let end_code: u16 = clear_code + 1;
    let code_size: u8 = min_code_size + 1;
    let mut out = Vec::<u8>::new();
    let mut bit_buffer: u32 = 0;
    let mut bit_count: u8 = 0;

    let emit = |code: u16, out: &mut Vec<u8>, bit_buffer: &mut u32, bit_count: &mut u8| {
        *bit_buffer |= (code as u32) << (*bit_count as u32);
        *bit_count += code_size;
        while *bit_count >= 8 {
            out.push((*bit_buffer & 0xFF) as u8);
            *bit_buffer >>= 8;
            *bit_count -= 8;
        }
    };

    emit(clear_code, &mut out, &mut bit_buffer, &mut bit_count);
    for &v in data {
        emit(v as u16, &mut out, &mut bit_buffer, &mut bit_count);
        emit(clear_code, &mut out, &mut bit_buffer, &mut bit_count);
    }
    emit(end_code, &mut out, &mut bit_buffer, &mut bit_count);
    if bit_count > 0 {
        out.push((bit_buffer & 0xFF) as u8);
    }
    out
}

fn py_save_gif(
    path: &str,
    width: i64,
    height: i64,
    frames: &[Vec<u8>],
    palette: &[u8],
    delay_cs: i64,
    loop_count: i64,
) {
    if palette.len() != 256 * 3 {
        panic!("palette must be 256*3 bytes");
    }
    let w = width as usize;
    let h = height as usize;
    for fr in frames.iter() {
        if fr.len() != w * h {
            panic!("frame size mismatch");
        }
    }

    let mut out = Vec::<u8>::new();
    out.extend_from_slice(b"GIF89a");
    out.extend_from_slice(&(width as u16).to_le_bytes());
    out.extend_from_slice(&(height as u16).to_le_bytes());
    out.push(0xF7);
    out.push(0);
    out.push(0);
    out.extend_from_slice(palette);

    out.extend_from_slice(b"\\x21\\xFF\\x0BNETSCAPE2.0\\x03\\x01");
    out.extend_from_slice(&(loop_count as u16).to_le_bytes());
    out.push(0);

    for fr in frames.iter() {
        out.extend_from_slice(b"\\x21\\xF9\\x04\\x00");
        out.extend_from_slice(&(delay_cs as u16).to_le_bytes());
        out.extend_from_slice(b"\\x00\\x00");

        out.push(0x2C);
        out.extend_from_slice(&(0u16).to_le_bytes());
        out.extend_from_slice(&(0u16).to_le_bytes());
        out.extend_from_slice(&(width as u16).to_le_bytes());
        out.extend_from_slice(&(height as u16).to_le_bytes());
        out.push(0);

        out.push(8);
        let compressed = py_gif_lzw_encode(fr, 8);
        let mut pos = 0usize;
        while pos < compressed.len() {
            let remain = compressed.len() - pos;
            let chunk_len = if remain > 255 { 255 } else { remain };
            out.push(chunk_len as u8);
            out.extend_from_slice(&compressed[pos..(pos + chunk_len)]);
            pos += chunk_len;
        }
        out.push(0);
    }

    out.push(0x3B);
    let parent = std::path::Path::new(path).parent();
    if let Some(dir) = parent {
        let _ = fs::create_dir_all(dir);
    }
    let mut f = fs::File::create(path).expect("create gif file failed");
    f.write_all(&out).expect("write gif file failed");
}

mod time {
    pub fn perf_counter() -> f64 {
        super::py_perf_counter()
    }
}

mod math {
    pub const pi: f64 = ::std::f64::consts::PI;
    pub trait ToF64 {
        fn to_f64(self) -> f64;
    }
    impl ToF64 for f64 {
        fn to_f64(self) -> f64 { self }
    }
    impl ToF64 for f32 {
        fn to_f64(self) -> f64 { self as f64 }
    }
    impl ToF64 for i64 {
        fn to_f64(self) -> f64 { self as f64 }
    }
    impl ToF64 for i32 {
        fn to_f64(self) -> f64 { self as f64 }
    }
    impl ToF64 for i16 {
        fn to_f64(self) -> f64 { self as f64 }
    }
    impl ToF64 for i8 {
        fn to_f64(self) -> f64 { self as f64 }
    }
    impl ToF64 for u64 {
        fn to_f64(self) -> f64 { self as f64 }
    }
    impl ToF64 for u32 {
        fn to_f64(self) -> f64 { self as f64 }
    }
    impl ToF64 for u16 {
        fn to_f64(self) -> f64 { self as f64 }
    }
    impl ToF64 for u8 {
        fn to_f64(self) -> f64 { self as f64 }
    }
    impl ToF64 for usize {
        fn to_f64(self) -> f64 { self as f64 }
    }
    impl ToF64 for isize {
        fn to_f64(self) -> f64 { self as f64 }
    }

    pub fn sin<T: ToF64>(v: T) -> f64 { v.to_f64().sin() }
    pub fn cos<T: ToF64>(v: T) -> f64 { v.to_f64().cos() }
    pub fn tan<T: ToF64>(v: T) -> f64 { v.to_f64().tan() }
    pub fn sqrt<T: ToF64>(v: T) -> f64 { v.to_f64().sqrt() }
    pub fn exp<T: ToF64>(v: T) -> f64 { v.to_f64().exp() }
    pub fn log<T: ToF64>(v: T) -> f64 { v.to_f64().ln() }
    pub fn log10<T: ToF64>(v: T) -> f64 { v.to_f64().log10() }
    pub fn fabs<T: ToF64>(v: T) -> f64 { v.to_f64().abs() }
    pub fn floor<T: ToF64>(v: T) -> f64 { v.to_f64().floor() }
    pub fn ceil<T: ToF64>(v: T) -> f64 { v.to_f64().ceil() }
    pub fn pow(a: f64, b: f64) -> f64 { a.powf(b) }
}

mod pytra {
    pub mod runtime {
        pub mod png {
            pub fn write_rgb_png(path: impl AsRef<str>, width: i64, height: i64, pixels: &[u8]) {
                super::super::super::py_write_rgb_png(path.as_ref(), width, height, pixels);
            }
        }

        pub mod gif {
            pub fn grayscale_palette() -> Vec<u8> {
                super::super::super::py_grayscale_palette()
            }

            pub fn save_gif(
                path: impl AsRef<str>,
                width: i64,
                height: i64,
                frames: &[Vec<u8>],
                palette: &[u8],
                delay_cs: i64,
                loop_count: i64,
            ) {
                super::super::super::py_save_gif(
                    path.as_ref(),
                    width,
                    height,
                    frames,
                    palette,
                    delay_cs,
                    loop_count,
                );
            }
        }
    }

    pub mod utils {
        pub use super::runtime::gif;
        pub use super::runtime::png;
    }
}
"""


def load_rs_profile() -> dict[str, Any]:
    """Rust 用 profile を読み込む。"""
    return CodeEmitter.load_profile_with_includes(
        "src/profiles/rs/profile.json",
        anchor_file=__file__,
    )


def load_rs_hooks(profile: dict[str, Any]) -> dict[str, Any]:
    """Rust 用 hook を読み込む。"""
    _ = profile
    hooks = build_rs_hooks()
    if isinstance(hooks, dict):
        return hooks
    return {}


class RustEmitter(CodeEmitter):
    """EAST を Rust ソースへ変換する最小エミッタ。"""

    def __init__(self, east_doc: dict[str, Any]) -> None:
        profile = load_rs_profile()
        hooks = load_rs_hooks(profile)
        self.init_base_state(east_doc, profile, hooks)
        self.type_map = self.load_type_map(profile)
        operators = self.any_to_dict_or_empty(profile.get("operators"))
        self.bin_ops = self.any_to_str_dict_or_empty(operators.get("binop"))
        self.cmp_ops = self.any_to_str_dict_or_empty(operators.get("cmp"))
        self.aug_ops = self.any_to_str_dict_or_empty(operators.get("aug"))
        syntax = self.any_to_dict_or_empty(profile.get("syntax"))
        identifiers = self.any_to_dict_or_empty(syntax.get("identifiers"))
        self.reserved_words: set[str] = set(self.any_to_str_list(identifiers.get("reserved_words")))
        self.rename_prefix = self.any_to_str(identifiers.get("rename_prefix"))
        if self.rename_prefix == "":
            self.rename_prefix = "py_"
        self.function_return_types: dict[str, str] = {}
        self.class_names: set[str] = set()
        self.class_base_map: dict[str, str] = {}
        self.class_field_types: dict[str, dict[str, str]] = {}
        self.class_method_mutability: dict[str, dict[str, bool]] = {}
        self.function_arg_ref_modes: dict[str, list[bool]] = {}
        self.class_method_arg_ref_modes: dict[str, dict[str, list[bool]]] = {}
        self.class_type_id_map: dict[str, int] = {}
        self.type_info_map: dict[int, tuple[int, int, int]] = {}
        self.declared_var_types: dict[str, str] = {}
        self.uses_pyany: bool = False
        self.uses_isinstance_runtime: bool = False
        self.current_fn_write_counts: dict[str, int] = {}
        self.current_fn_mutating_call_counts: dict[str, int] = {}
        self.current_ref_vars: set[str] = set()
        self.uses_string_helpers: bool = False

    def get_expr_type(self, expr: Any) -> str:
        """解決済み型 + ローカル宣言テーブルで式型を返す。"""
        t = super().get_expr_type(expr)
        if t not in {"", "unknown"}:
            return t
        node = self.any_to_dict_or_empty(expr)
        if self.any_dict_get_str(node, "kind", "") == "Name":
            name = self.any_dict_get_str(node, "id", "")
            if name in self.declared_var_types:
                return self.normalize_type_name(self.declared_var_types[name])
        return t

    def _safe_name(self, name: str) -> str:
        if name == "self":
            return "self"
        if name == "_":
            return "py_underscore"
        if name == "main" and "__pytra_main" in self.function_return_types and "main" not in self.function_return_types:
            return "__pytra_main"
        return self.rename_if_reserved(name, self.reserved_words, self.rename_prefix, {})

    def _increment_name_count(self, counts: dict[str, int], name: str) -> None:
        """識別子カウントを 1 増やす。"""
        if name == "":
            return
        if name in counts:
            counts[name] += 1
            return
        counts[name] = 1

    def _collect_store_name_counts_from_target(self, target: Any, counts: dict[str, int]) -> None:
        """代入 target から束縛名書き込み回数を収集する。"""
        if isinstance(target, dict):
            kind = self.any_dict_get_str(target, "kind", "")
            if kind == "Name":
                self._increment_name_count(counts, self.any_dict_get_str(target, "id", ""))
                return
            if kind == "Attribute" or kind == "Subscript":
                self._collect_store_name_counts_from_target(target.get("value"), counts)
                return
            if kind == "Tuple" or kind == "List":
                elems_obj: Any = target.get("elements")
                elems: list[Any] = elems_obj if isinstance(elems_obj, list) else []
                for elem in elems:
                    self._collect_store_name_counts_from_target(elem, counts)
                return
            return
        if isinstance(target, list):
            for item in target:
                self._collect_store_name_counts_from_target(item, counts)

    def _collect_name_write_counts(self, stmts: list[dict[str, Any]]) -> dict[str, int]:
        """関数本文の書き込み回数（束縛名単位）を収集する。"""
        out: dict[str, int] = {}
        for st in stmts:
            if not isinstance(st, dict):
                continue
            kind = self.any_dict_get_str(st, "kind", "")
            if kind == "FunctionDef" or kind == "ClassDef":
                continue
            if kind == "Assign" or kind == "AnnAssign" or kind == "AugAssign":
                self._collect_store_name_counts_from_target(st.get("target"), out)
                continue
            if kind == "Swap":
                self._collect_store_name_counts_from_target(st.get("left"), out)
                self._collect_store_name_counts_from_target(st.get("right"), out)
                continue
            if kind == "For" or kind == "ForRange":
                self._collect_store_name_counts_from_target(st.get("target"), out)
                body_obj: Any = st.get("body")
                body: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
                body_counts = self._collect_name_write_counts(body)
                for name, cnt in body_counts.items():
                    out[name] = out.get(name, 0) + cnt
                orelse_obj: Any = st.get("orelse")
                orelse: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
                orelse_counts = self._collect_name_write_counts(orelse)
                for name, cnt in orelse_counts.items():
                    out[name] = out.get(name, 0) + cnt
                continue
            if kind == "If" or kind == "While":
                body_obj = st.get("body")
                body = body_obj if isinstance(body_obj, list) else []
                body_counts = self._collect_name_write_counts(body)
                for name, cnt in body_counts.items():
                    out[name] = out.get(name, 0) + cnt
                orelse_obj = st.get("orelse")
                orelse = orelse_obj if isinstance(orelse_obj, list) else []
                orelse_counts = self._collect_name_write_counts(orelse)
                for name, cnt in orelse_counts.items():
                    out[name] = out.get(name, 0) + cnt
                continue
            if kind == "Try":
                body_obj = st.get("body")
                body = body_obj if isinstance(body_obj, list) else []
                body_counts = self._collect_name_write_counts(body)
                for name, cnt in body_counts.items():
                    out[name] = out.get(name, 0) + cnt
                orelse_obj = st.get("orelse")
                orelse = orelse_obj if isinstance(orelse_obj, list) else []
                orelse_counts = self._collect_name_write_counts(orelse)
                for name, cnt in orelse_counts.items():
                    out[name] = out.get(name, 0) + cnt
                final_obj = st.get("finalbody")
                finalbody = final_obj if isinstance(final_obj, list) else []
                final_counts = self._collect_name_write_counts(finalbody)
                for name, cnt in final_counts.items():
                    out[name] = out.get(name, 0) + cnt
                handlers_obj: Any = st.get("handlers")
                handlers: list[dict[str, Any]] = handlers_obj if isinstance(handlers_obj, list) else []
                for handler in handlers:
                    if not isinstance(handler, dict):
                        continue
                    h_name = handler.get("name")
                    if isinstance(h_name, str) and h_name != "":
                        self._increment_name_count(out, h_name)
                    h_body_obj: Any = handler.get("body")
                    h_body: list[dict[str, Any]] = h_body_obj if isinstance(h_body_obj, list) else []
                    h_counts = self._collect_name_write_counts(h_body)
                    for name, cnt in h_counts.items():
                        out[name] = out.get(name, 0) + cnt
        return out

    def _expr_mentions_name(self, node: Any, name: str) -> bool:
        """式/文サブツリーに `Name(name)` が含まれるかを返す。"""
        if isinstance(node, dict):
            if self.any_dict_get_str(node, "kind", "") == "Name" and self.any_dict_get_str(node, "id", "") == name:
                return True
            for _k, v in node.items():
                if self._expr_mentions_name(v, name):
                    return True
            return False
        if isinstance(node, list):
            for item in node:
                if self._expr_mentions_name(item, name):
                    return True
        return False

    def _mutating_method_names(self) -> set[str]:
        return {
            "append",
            "pop",
            "clear",
            "insert",
            "remove",
            "sort",
            "reverse",
            "extend",
            "update",
            "setdefault",
            "add",
            "discard",
        }

    def _all_mutating_class_method_names(self) -> set[str]:
        """既知クラスで `&mut self` が必要なメソッド名集合を返す。"""
        out: set[str] = set()
        for _cls, method_map in self.class_method_mutability.items():
            for name, is_mut in method_map.items():
                if is_mut:
                    out.add(name)
        return out

    def _should_pass_arg_by_ref_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        if t == "str" or t in {"bytes", "bytearray"}:
            return True
        if t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple["):
            return True
        if t in self.class_names:
            return True
        return False

    def _should_pass_method_arg_by_ref_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        if t == "str" or t in {"bytes", "bytearray"}:
            return True
        if t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple["):
            return True
        return False

    def _compute_function_arg_ref_modes(self, fn: dict[str, Any], *, for_method: bool = False) -> list[bool]:
        """関数の各引数を `&T` で受けるべきかを返す（top-level 用）。"""
        arg_order = self.any_to_str_list(fn.get("arg_order"))
        arg_types = self.any_to_dict_or_empty(fn.get("arg_types"))
        arg_usage = self.any_to_dict_or_empty(fn.get("arg_usage"))
        body = self._dict_stmt_list(fn.get("body"))
        write_counts = self._collect_name_write_counts(body)
        mut_call_counts = self._collect_mutating_receiver_name_counts(body)
        pass_by_ref_pred = self._should_pass_method_arg_by_ref_type if for_method else self._should_pass_arg_by_ref_type
        modes: list[bool] = []
        for arg_name in arg_order:
            if arg_name == "self":
                continue
            usage = self.any_to_str(arg_usage.get(arg_name))
            write_count = write_counts.get(arg_name, 0)
            mut_call_count = mut_call_counts.get(arg_name, 0)
            is_mut = usage == "reassigned" or usage == "mutable" or usage == "write" or write_count > 0 or mut_call_count > 0
            modes.append((not is_mut) and pass_by_ref_pred(self.any_to_str(arg_types.get(arg_name))))
        return modes

    def _receiver_root_name(self, node: dict[str, Any]) -> str:
        """Attribute 連鎖の最左端 Name を返す。見つからなければ空文字。"""
        cur = self.any_to_dict_or_empty(node)
        while self.any_dict_get_str(cur, "kind", "") == "Attribute":
            cur = self.any_to_dict_or_empty(cur.get("value"))
        if self.any_dict_get_str(cur, "kind", "") == "Name":
            return self.any_dict_get_str(cur, "id", "")
        return ""

    def _collect_self_called_methods_from_expr(self, node: Any, out: set[str]) -> None:
        """式木から `self.method(...)` 呼び出しの method 名を収集する。"""
        if isinstance(node, dict):
            if self.any_dict_get_str(node, "kind", "") == "Call":
                fn = self.any_to_dict_or_empty(node.get("func"))
                if self.any_dict_get_str(fn, "kind", "") == "Attribute":
                    owner = self.any_to_dict_or_empty(fn.get("value"))
                    if self.any_dict_get_str(owner, "kind", "") == "Name" and self.any_dict_get_str(owner, "id", "") == "self":
                        attr = self.any_dict_get_str(fn, "attr", "")
                        if attr != "":
                            out.add(attr)
            for _k, v in node.items():
                self._collect_self_called_methods_from_expr(v, out)
            return
        if isinstance(node, list):
            for item in node:
                self._collect_self_called_methods_from_expr(item, out)

    def _collect_self_called_methods(self, stmts: list[dict[str, Any]]) -> set[str]:
        """文リスト中の `self.method(...)` 呼び出し集合を返す。"""
        out: set[str] = set()
        for st in stmts:
            self._collect_self_called_methods_from_expr(st, out)
        return out

    def _analyze_class_method_mutability(self, members: list[dict[str, Any]]) -> dict[str, bool]:
        """クラス内メソッドの `self` 可変性を固定点で推定する。"""
        method_bodies: dict[str, list[dict[str, Any]]] = {}
        mut_map: dict[str, bool] = {}
        deps: dict[str, set[str]] = {}
        for member in members:
            if self.any_dict_get_str(member, "kind", "") != "FunctionDef":
                continue
            name = self.any_to_str(member.get("name"))
            if name == "":
                continue
            body = self._dict_stmt_list(member.get("body"))
            method_bodies[name] = body
            writes = self._collect_name_write_counts(body)
            mut_calls = self._collect_mutating_receiver_name_counts(body)
            mut_map[name] = writes.get("self", 0) > 0 or mut_calls.get("self", 0) > 0
            deps[name] = self._collect_self_called_methods(body)

        changed = True
        while changed:
            changed = False
            for name, called in deps.items():
                if mut_map.get(name, False):
                    continue
                for callee in called:
                    if mut_map.get(callee, False):
                        mut_map[name] = True
                        changed = True
                        break
        return mut_map

    def _count_self_calls_to_mut_methods(self, stmts: list[dict[str, Any]], method_mut_map: dict[str, bool]) -> int:
        """本文中の `self.<mut_method>()` 呼び出し数を返す。"""
        called = self._collect_self_called_methods(stmts)
        count = 0
        for name in called:
            if method_mut_map.get(name, False):
                count += 1
        return count

    def _collect_mutating_call_counts_from_expr(self, node: Any, out: dict[str, int]) -> None:
        """破壊的メソッド呼び出し receiver 名の出現回数を収集する。"""
        if isinstance(node, dict):
            kind = self.any_dict_get_str(node, "kind", "")
            if kind == "Call":
                fn = self.any_to_dict_or_empty(node.get("func"))
                if self.any_dict_get_str(fn, "kind", "") == "Attribute":
                    attr = self.any_dict_get_str(fn, "attr", "")
                    owner = self.any_to_dict_or_empty(fn.get("value"))
                    owner_name = self._receiver_root_name(owner)
                    if owner_name != "":
                        if attr in self._mutating_method_names():
                            self._increment_name_count(out, owner_name)
                        if attr in self._all_mutating_class_method_names():
                            self._increment_name_count(out, owner_name)
                        root_owner: dict[str, Any] = {"kind": "Name", "id": owner_name}
                        owner_t = self.normalize_type_name(self.get_expr_type(root_owner))
                        if owner_t in self.class_names:
                            self._increment_name_count(out, owner_name)
            for _k, v in node.items():
                self._collect_mutating_call_counts_from_expr(v, out)
            return
        if isinstance(node, list):
            for item in node:
                self._collect_mutating_call_counts_from_expr(item, out)

    def _collect_mutating_receiver_name_counts(self, stmts: list[dict[str, Any]]) -> dict[str, int]:
        """関数本文から破壊的メソッド呼び出し receiver 名を収集する。"""
        out: dict[str, int] = {}
        for st in stmts:
            if not isinstance(st, dict):
                continue
            kind = self.any_dict_get_str(st, "kind", "")
            if kind == "FunctionDef" or kind == "ClassDef":
                continue
            if kind == "If" or kind == "While" or kind == "For" or kind == "ForRange":
                self._collect_mutating_call_counts_from_expr(st.get("test"), out)
                self._collect_mutating_call_counts_from_expr(st.get("iter"), out)
                self._collect_mutating_call_counts_from_expr(st.get("start"), out)
                self._collect_mutating_call_counts_from_expr(st.get("stop"), out)
                self._collect_mutating_call_counts_from_expr(st.get("step"), out)
                body_obj: Any = st.get("body")
                body: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
                body_counts = self._collect_mutating_receiver_name_counts(body)
                for name, cnt in body_counts.items():
                    out[name] = out.get(name, 0) + cnt
                orelse_obj: Any = st.get("orelse")
                orelse: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
                orelse_counts = self._collect_mutating_receiver_name_counts(orelse)
                for name, cnt in orelse_counts.items():
                    out[name] = out.get(name, 0) + cnt
                continue
            if kind == "Try":
                body_obj = st.get("body")
                body = body_obj if isinstance(body_obj, list) else []
                body_counts = self._collect_mutating_receiver_name_counts(body)
                for name, cnt in body_counts.items():
                    out[name] = out.get(name, 0) + cnt
                orelse_obj = st.get("orelse")
                orelse = orelse_obj if isinstance(orelse_obj, list) else []
                orelse_counts = self._collect_mutating_receiver_name_counts(orelse)
                for name, cnt in orelse_counts.items():
                    out[name] = out.get(name, 0) + cnt
                final_obj = st.get("finalbody")
                finalbody = final_obj if isinstance(final_obj, list) else []
                final_counts = self._collect_mutating_receiver_name_counts(finalbody)
                for name, cnt in final_counts.items():
                    out[name] = out.get(name, 0) + cnt
                handlers_obj: Any = st.get("handlers")
                handlers: list[dict[str, Any]] = handlers_obj if isinstance(handlers_obj, list) else []
                for handler in handlers:
                    if not isinstance(handler, dict):
                        continue
                    h_body_obj: Any = handler.get("body")
                    h_body: list[dict[str, Any]] = h_body_obj if isinstance(h_body_obj, list) else []
                    h_counts = self._collect_mutating_receiver_name_counts(h_body)
                    for name, cnt in h_counts.items():
                        out[name] = out.get(name, 0) + cnt
                continue
            self._collect_mutating_call_counts_from_expr(st, out)
        return out

    def _should_declare_mut(self, name_raw: str, has_init_write: bool) -> bool:
        """現在関数内の書き込み情報から `let mut` 必要性を判定する。"""
        write_count = self.current_fn_write_counts.get(name_raw, 0)
        mut_call_count = self.current_fn_mutating_call_counts.get(name_raw, 0)
        threshold = 1 if has_init_write else 0
        if write_count > threshold:
            return True
        if mut_call_count > 0:
            return True
        return False

    def _doc_mentions_any(self, node: Any) -> bool:
        """EAST 全体に `Any/object` 型が含まれるかを粗く判定する。"""
        if isinstance(node, dict):
            for _k, v in node.items():
                if self._doc_mentions_any(v):
                    return True
            return False
        if isinstance(node, list):
            for item in node:
                if self._doc_mentions_any(item):
                    return True
            return False
        if isinstance(node, str):
            t = self.normalize_type_name(node)
            if t == "Any" or t == "object":
                return True
            if self._contains_text(t, "Any") or self._contains_text(t, "object"):
                return True
        return False

    def _doc_mentions_isinstance(self, node: Any) -> bool:
        """EAST 全体に `isinstance(...)` 呼び出しが含まれるかを判定する。"""
        if isinstance(node, dict):
            if self.any_dict_get_str(node, "kind", "") == "Call":
                fn = self.any_to_dict_or_empty(node.get("func"))
                if self.any_dict_get_str(fn, "kind", "") == "Name" and self.any_dict_get_str(fn, "id", "") == "isinstance":
                    return True
            for _k, v in node.items():
                if self._doc_mentions_isinstance(v):
                    return True
            return False
        if isinstance(node, list):
            for item in node:
                if self._doc_mentions_isinstance(item):
                    return True
            return False
        return False

    def _builtin_type_id_expr(self, type_name: str) -> str:
        """型名を Rust runtime の `PYTRA_TID_*` 定数式へ変換する。"""
        t = self.normalize_type_name(type_name)
        if t == "None":
            return "PYTRA_TID_NONE"
        if t == "bool":
            return "PYTRA_TID_BOOL"
        if t == "int" or self._is_int_type(t):
            return "PYTRA_TID_INT"
        if t == "float" or self._is_float_type(t):
            return "PYTRA_TID_FLOAT"
        if t == "str":
            return "PYTRA_TID_STR"
        if t == "bytes" or t == "bytearray" or t.startswith("list[") or t == "list":
            return "PYTRA_TID_LIST"
        if t.startswith("dict[") or t == "dict":
            return "PYTRA_TID_DICT"
        if t.startswith("set[") or t == "set":
            return "PYTRA_TID_SET"
        if t == "object":
            return "PYTRA_TID_OBJECT"
        if t in self.class_names:
            return self._safe_name(t) + "::PYTRA_TYPE_ID"
        return ""

    def _base_type_id_for_name(self, base_name: str) -> int:
        """基底型名を type_id へ変換する（未知は object）。"""
        expr = self._builtin_type_id_expr(base_name)
        if expr == "PYTRA_TID_NONE":
            return 0
        if expr == "PYTRA_TID_BOOL":
            return 1
        if expr == "PYTRA_TID_INT":
            return 2
        if expr == "PYTRA_TID_FLOAT":
            return 3
        if expr == "PYTRA_TID_STR":
            return 4
        if expr == "PYTRA_TID_LIST":
            return 5
        if expr == "PYTRA_TID_DICT":
            return 6
        if expr == "PYTRA_TID_SET":
            return 7
        if expr == "PYTRA_TID_OBJECT":
            return 8
        normalized = self.normalize_type_name(base_name)
        if normalized in self.class_type_id_map:
            return self.class_type_id_map[normalized]
        return 8

    def _prepare_type_id_table(self) -> None:
        """Rust 出力に埋め込む `type_id` 範囲テーブルを計算する。"""
        self.class_type_id_map = {}
        self.type_info_map = {}

        type_ids: list[int] = []
        type_base: dict[int, int] = {}
        type_children: dict[int, list[int]] = {}

        def _register(tid: int, base_tid: int) -> None:
            if tid not in type_ids:
                type_ids.append(tid)
            prev_base = type_base.get(tid, -1)
            if prev_base >= 0 and prev_base in type_children:
                prev_children = type_children[prev_base]
                if tid in prev_children:
                    prev_children.remove(tid)
            type_base[tid] = base_tid
            if tid not in type_children:
                type_children[tid] = []
            if base_tid < 0:
                return
            if base_tid not in type_children:
                type_children[base_tid] = []
            children = type_children[base_tid]
            if tid not in children:
                children.append(tid)

        # built-in hierarchy: object <- {int(bool), float, str, list, dict, set}
        _register(0, -1)
        _register(8, -1)
        _register(2, 8)
        _register(1, 2)
        _register(3, 8)
        _register(4, 8)
        _register(5, 8)
        _register(6, 8)
        _register(7, 8)

        next_user_tid = 1000
        for class_name in sorted(self.class_names):
            while next_user_tid in type_base:
                next_user_tid += 1
            self.class_type_id_map[class_name] = next_user_tid
            next_user_tid += 1

        for class_name in sorted(self.class_names):
            tid = self.class_type_id_map[class_name]
            base_name = self.normalize_type_name(self.class_base_map.get(class_name, ""))
            if base_name == "":
                base_name = "object"
            _register(tid, self._base_type_id_for_name(base_name))

        def _sorted_ints(items: list[int]) -> list[int]:
            out = list(items)
            out.sort()
            return out

        def _collect_roots() -> list[int]:
            roots: list[int] = []
            for tid in type_ids:
                base_tid = type_base.get(tid, -1)
                if base_tid < 0 or base_tid not in type_base:
                    roots.append(tid)
            return _sorted_ints(roots)

        type_order: dict[int, int] = {}
        type_min: dict[int, int] = {}
        type_max: dict[int, int] = {}

        def _assign_dfs(tid: int, next_order: int) -> int:
            type_order[tid] = next_order
            type_min[tid] = next_order
            cur = next_order + 1
            for child_tid in _sorted_ints(type_children.get(tid, [])):
                cur = _assign_dfs(child_tid, cur)
            type_max[tid] = cur - 1
            return cur

        next_order = 0
        for root_tid in _collect_roots():
            next_order = _assign_dfs(root_tid, next_order)
        for tid in _sorted_ints(type_ids):
            if tid not in type_order:
                next_order = _assign_dfs(tid, next_order)

        for tid in _sorted_ints(type_ids):
            self.type_info_map[tid] = (
                type_order[tid],
                type_min[tid],
                type_max[tid],
            )

    def _emit_isinstance_runtime_helpers(self) -> None:
        """`isinstance` 用 `type_id` runtime helper を出力する。"""
        self.emit("const PYTRA_TID_NONE: i64 = 0;")
        self.emit("const PYTRA_TID_BOOL: i64 = 1;")
        self.emit("const PYTRA_TID_INT: i64 = 2;")
        self.emit("const PYTRA_TID_FLOAT: i64 = 3;")
        self.emit("const PYTRA_TID_STR: i64 = 4;")
        self.emit("const PYTRA_TID_LIST: i64 = 5;")
        self.emit("const PYTRA_TID_DICT: i64 = 6;")
        self.emit("const PYTRA_TID_SET: i64 = 7;")
        self.emit("const PYTRA_TID_OBJECT: i64 = 8;")
        self.emit("")
        self.emit("#[derive(Clone, Copy)]")
        self.emit("struct PyTypeInfo {")
        self.indent += 1
        self.emit("order: i64,")
        self.emit("min: i64,")
        self.emit("max: i64,")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_type_info(type_id: i64) -> Option<PyTypeInfo> {")
        self.indent += 1
        self.emit("match type_id {")
        self.indent += 1
        for tid in sorted(self.type_info_map.keys()):
            order, min_id, max_id = self.type_info_map[tid]
            self.emit(
                f"{tid} => Some(PyTypeInfo {{ order: {order}, min: {min_id}, max: {max_id} }}),"
            )
        self.emit("_ => None,")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("trait PyRuntimeTypeId {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64;")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl PyRuntimeTypeId for bool {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("PYTRA_TID_BOOL")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl PyRuntimeTypeId for i64 {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("PYTRA_TID_INT")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl PyRuntimeTypeId for f64 {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("PYTRA_TID_FLOAT")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl PyRuntimeTypeId for String {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("PYTRA_TID_STR")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl<T> PyRuntimeTypeId for Vec<T> {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("PYTRA_TID_LIST")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl<K: Ord, V> PyRuntimeTypeId for ::std::collections::BTreeMap<K, V> {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("PYTRA_TID_DICT")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl<T: Ord> PyRuntimeTypeId for ::std::collections::BTreeSet<T> {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("PYTRA_TID_SET")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("impl<T: PyRuntimeTypeId> PyRuntimeTypeId for Option<T> {")
        self.indent += 1
        self.emit("fn py_runtime_type_id(&self) -> i64 {")
        self.indent += 1
        self.emit("match self {")
        self.indent += 1
        self.emit("Some(v) => v.py_runtime_type_id(),")
        self.emit("None => PYTRA_TID_NONE,")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        if self.uses_pyany:
            self.emit("")
            self.emit("impl PyRuntimeTypeId for PyAny {")
            self.indent += 1
            self.emit("fn py_runtime_type_id(&self) -> i64 {")
            self.indent += 1
            self.emit("match self {")
            self.indent += 1
            self.emit("PyAny::Int(_) => PYTRA_TID_INT,")
            self.emit("PyAny::Float(_) => PYTRA_TID_FLOAT,")
            self.emit("PyAny::Bool(_) => PYTRA_TID_BOOL,")
            self.emit("PyAny::Str(_) => PYTRA_TID_STR,")
            self.emit("PyAny::List(_) => PYTRA_TID_LIST,")
            self.emit("PyAny::Dict(_) => PYTRA_TID_DICT,")
            self.emit("PyAny::Set(_) => PYTRA_TID_SET,")
            self.emit("PyAny::None => PYTRA_TID_NONE,")
            self.indent -= 1
            self.emit("}")
            self.indent -= 1
            self.emit("}")
            self.indent -= 1
            self.emit("}")
        self.emit("")
        self.emit("fn py_runtime_type_id<T: PyRuntimeTypeId>(value: &T) -> i64 {")
        self.indent += 1
        self.emit("value.py_runtime_type_id()")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_is_subtype(actual_type_id: i64, expected_type_id: i64) -> bool {")
        self.indent += 1
        self.emit("let actual = match py_type_info(actual_type_id) {")
        self.indent += 1
        self.emit("Some(info) => info,")
        self.emit("None => return false,")
        self.indent -= 1
        self.emit("};")
        self.emit("let expected = match py_type_info(expected_type_id) {")
        self.indent += 1
        self.emit("Some(info) => info,")
        self.emit("None => return false,")
        self.indent -= 1
        self.emit("};")
        self.emit("expected.min <= actual.order && actual.order <= expected.max")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_issubclass(actual_type_id: i64, expected_type_id: i64) -> bool {")
        self.indent += 1
        self.emit("py_is_subtype(actual_type_id, expected_type_id)")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_isinstance<T: PyRuntimeTypeId>(value: &T, expected_type_id: i64) -> bool {")
        self.indent += 1
        self.emit("py_is_subtype(py_runtime_type_id(value), expected_type_id)")
        self.indent -= 1
        self.emit("}")

    def _is_any_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        return t == "Any" or t == "object"

    def _is_int_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        return t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}

    def _is_float_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        return t in {"float32", "float64"}

    def _list_elem_type(self, east_type: str) -> str:
        t = self.normalize_type_name(east_type)
        if not t.startswith("list[") or not t.endswith("]"):
            return ""
        parts = self.split_generic(t[5:-1].strip())
        if len(parts) != 1:
            return ""
        return self.normalize_type_name(parts[0])

    def _can_borrow_iter_node(self, iter_node: Any) -> bool:
        """for/enumerate の反復対象を借用で回して良いかを保守的に判定する。"""
        d = self.any_to_dict_or_empty(iter_node)
        if self.any_dict_get_str(d, "kind", "") != "Name":
            return True
        name_raw = self.any_dict_get_str(d, "id", "")
        if name_raw == "":
            return False
        write_count = self.current_fn_write_counts.get(name_raw, 0)
        mut_call_count = self.current_fn_mutating_call_counts.get(name_raw, 0)
        return write_count == 0 and mut_call_count == 0

    def _render_list_iter_expr(self, list_expr: str, list_type: str, can_borrow: bool) -> str:
        """list 反復の Rust 式を生成する（必要最小限の clone/copy に寄せる）。"""
        elem_t = self._list_elem_type(list_type)
        if self._is_copy_type(elem_t):
            return "(" + list_expr + ").iter().copied()"
        if can_borrow and (elem_t in self.class_names or elem_t == "str"):
            return "(" + list_expr + ").iter()"
        return "(" + list_expr + ").iter().cloned()"

    def _is_copy_type(self, east_type: str) -> bool:
        t = self.normalize_type_name(east_type)
        if self._is_int_type(t):
            return True
        if self._is_float_type(t):
            return True
        return t in {"bool", "char", "int", "float", "usize", "isize"}

    def _string_constant_literal(self, node: Any) -> str:
        d = self.any_to_dict_or_empty(node)
        if self.any_dict_get_str(d, "kind", "") != "Constant":
            return ""
        v = d.get("value")
        if not isinstance(v, str):
            return ""
        return self.quote_string_literal(v)

    def _is_fully_parenthesized(self, text: str) -> bool:
        if len(text) < 2 or not text.startswith("(") or not text.endswith(")"):
            return False
        depth = 0
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i != len(text) - 1:
                    return False
                if depth < 0:
                    return False
            i += 1
        return depth == 0

    def _strip_outer_parens(self, text: str) -> str:
        out = text.strip()
        while self._is_fully_parenthesized(out):
            out = out[1:-1].strip()
        return out

    def _ensure_string_owned(self, text: str) -> str:
        expr_trim = self._strip_outer_parens(text)
        if expr_trim.endswith(".to_string()") or expr_trim.endswith(".to_owned()"):
            return text
        if expr_trim.startswith("String::from("):
            return text
        return "((" + text + ").to_string())"

    def _dict_key_value_types(self, east_type: str) -> tuple[str, str]:
        t = self.normalize_type_name(east_type)
        if not t.startswith("dict[") or not t.endswith("]"):
            return "", ""
        parts = self.split_generic(t[5:-1].strip())
        if len(parts) != 2:
            return "", ""
        return self.normalize_type_name(parts[0]), self.normalize_type_name(parts[1])

    def _coerce_dict_key_expr(self, key_expr: str, key_type: str, require_owned: bool = True) -> str:
        """dict key 型に合わせて key 式を補正する。"""
        if self.normalize_type_name(key_type) == "str":
            if require_owned:
                return self._ensure_string_owned(key_expr)
            return key_expr
        return key_expr

    def _is_dict_with_any_value(self, east_type: str) -> bool:
        key_t, val_t = self._dict_key_value_types(east_type)
        _ = key_t
        return self._is_any_type(val_t)

    def _dict_get_owner_value_type(self, call_node: Any) -> str:
        """`dict.get(...)` 呼び出しなら owner の value 型を返す。"""
        call_d = self.any_to_dict_or_empty(call_node)
        if self.any_dict_get_str(call_d, "kind", "") != "Call":
            return ""
        fn = self.any_to_dict_or_empty(call_d.get("func"))
        if self.any_dict_get_str(fn, "kind", "") != "Attribute":
            return ""
        if self.any_dict_get_str(fn, "attr", "") != "get":
            return ""
        owner = self.any_to_dict_or_empty(fn.get("value"))
        owner_t = self.normalize_type_name(self.get_expr_type(owner))
        if owner_t.startswith("dict["):
            _key_t, val_t = self._dict_key_value_types(owner_t)
            return val_t
        return ""

    def _dict_items_owner_type(self, call_node: Any) -> str:
        """`dict.items()` 呼び出しなら owner の dict 型を返す。"""
        call_d = self.any_to_dict_or_empty(call_node)
        if self.any_dict_get_str(call_d, "kind", "") != "Call":
            return ""
        fn = self.any_to_dict_or_empty(call_d.get("func"))
        if self.any_dict_get_str(fn, "kind", "") != "Attribute":
            return ""
        if self.any_dict_get_str(fn, "attr", "") != "items":
            return ""
        owner = self.any_to_dict_or_empty(fn.get("value"))
        owner_t = self.normalize_type_name(self.get_expr_type(owner))
        if owner_t.startswith("dict["):
            return owner_t
        return ""

    def _emit_pyany_runtime(self) -> None:
        """Any/object 用の最小ランタイム（PyAny）を出力する。"""
        self.emit("#[derive(Clone, Debug, Default)]")
        self.emit("enum PyAny {")
        self.indent += 1
        self.emit("Int(i64),")
        self.emit("Float(f64),")
        self.emit("Bool(bool),")
        self.emit("Str(String),")
        self.emit("Dict(::std::collections::BTreeMap<String, PyAny>),")
        self.emit("List(Vec<PyAny>),")
        self.emit("Set(Vec<PyAny>),")
        self.emit("#[default]")
        self.emit("None,")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_any_as_dict(v: PyAny) -> ::std::collections::BTreeMap<String, PyAny> {")
        self.indent += 1
        self.emit("match v {")
        self.indent += 1
        self.emit("PyAny::Dict(d) => d,")
        self.emit("_ => ::std::collections::BTreeMap::new(),")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_any_to_i64(v: &PyAny) -> i64 {")
        self.indent += 1
        self.emit("match v {")
        self.indent += 1
        self.emit("PyAny::Int(n) => *n,")
        self.emit("PyAny::Float(f) => *f as i64,")
        self.emit("PyAny::Bool(b) => if *b { 1 } else { 0 },")
        self.emit("PyAny::Str(s) => s.parse::<i64>().unwrap_or(0),")
        self.emit("_ => 0,")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_any_to_f64(v: &PyAny) -> f64 {")
        self.indent += 1
        self.emit("match v {")
        self.indent += 1
        self.emit("PyAny::Int(n) => *n as f64,")
        self.emit("PyAny::Float(f) => *f,")
        self.emit("PyAny::Bool(b) => if *b { 1.0 } else { 0.0 },")
        self.emit("PyAny::Str(s) => s.parse::<f64>().unwrap_or(0.0),")
        self.emit("_ => 0.0,")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_any_to_bool(v: &PyAny) -> bool {")
        self.indent += 1
        self.emit("match v {")
        self.indent += 1
        self.emit("PyAny::Int(n) => *n != 0,")
        self.emit("PyAny::Float(f) => *f != 0.0,")
        self.emit("PyAny::Bool(b) => *b,")
        self.emit("PyAny::Str(s) => !s.is_empty(),")
        self.emit("PyAny::Dict(d) => !d.is_empty(),")
        self.emit("PyAny::List(xs) => !xs.is_empty(),")
        self.emit("PyAny::Set(xs) => !xs.is_empty(),")
        self.emit("PyAny::None => false,")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("fn py_any_to_string(v: &PyAny) -> String {")
        self.indent += 1
        self.emit("match v {")
        self.indent += 1
        self.emit("PyAny::Int(n) => n.to_string(),")
        self.emit("PyAny::Float(f) => f.to_string(),")
        self.emit("PyAny::Bool(b) => b.to_string(),")
        self.emit("PyAny::Str(s) => s.clone(),")
        self.emit("PyAny::Dict(d) => format!(\"{:?}\", d),")
        self.emit("PyAny::List(xs) => format!(\"{:?}\", xs),")
        self.emit("PyAny::Set(xs) => format!(\"{:?}\", xs),")
        self.emit("PyAny::None => String::new(),")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")

    def _module_id_to_rust_use_path(self, module_id: str) -> str:
        """Python 形式モジュール名を Rust `use` パスへ変換する。"""
        if module_id == "":
            return ""
        return "crate::" + module_id.replace(".", "::")

    def _collect_use_lines(self, body: list[dict[str, Any]], meta: dict[str, Any]) -> list[str]:
        """import 情報を Rust `use` 行へ変換する。"""
        out: list[str] = []
        seen: set[str] = set()

        def _add(line: str) -> None:
            if line == "" or line in seen:
                return
            seen.add(line)
            out.append(line)

        bindings = self.any_to_dict_list(meta.get("import_bindings"))
        if len(bindings) > 0:
            i = 0
            while i < len(bindings):
                ent = bindings[i]
                binding_kind = self.any_to_str(ent.get("binding_kind"))
                module_id = self.any_to_str(ent.get("module_id"))
                local_name = self.any_to_str(ent.get("local_name"))
                export_name = self.any_to_str(ent.get("export_name"))
                if module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing", "dataclasses"}:
                    i += 1
                    continue
                if binding_kind == "module" and module_id == "math":
                    i += 1
                    continue
                base_path = self._module_id_to_rust_use_path(module_id)
                if binding_kind == "module" and base_path != "":
                    line = "use " + base_path
                    leaf = self._last_dotted_name(module_id)
                    if local_name != "" and local_name != leaf:
                        line += " as " + self._safe_name(local_name)
                    _add(line + ";")
                elif binding_kind == "symbol" and base_path != "" and export_name != "":
                    line = "use " + base_path + "::" + export_name
                    if local_name != "" and local_name != export_name:
                        line += " as " + self._safe_name(local_name)
                    _add(line + ";")
                i += 1
            return out

        for stmt in body:
            kind = self.any_dict_get_str(stmt, "kind", "")
            if kind == "Import":
                for ent in self._dict_stmt_list(stmt.get("names")):
                    module_id = self.any_to_str(ent.get("name"))
                    if module_id == "" or module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing", "dataclasses"}:
                        continue
                    if module_id == "math":
                        continue
                    base_path = self._module_id_to_rust_use_path(module_id)
                    if base_path == "":
                        continue
                    asname = self.any_to_str(ent.get("asname"))
                    line = "use " + base_path
                    leaf = self._last_dotted_name(module_id)
                    if asname != "" and asname != leaf:
                        line += " as " + self._safe_name(asname)
                    _add(line + ";")
            elif kind == "ImportFrom":
                module_id = self.any_to_str(stmt.get("module"))
                if module_id == "" or module_id.startswith("__future__") or module_id in {"typing", "pytra.std.typing", "dataclasses"}:
                    continue
                base_path = self._module_id_to_rust_use_path(module_id)
                if base_path == "":
                    continue
                for ent in self._dict_stmt_list(stmt.get("names")):
                    name = self.any_to_str(ent.get("name"))
                    if name == "":
                        continue
                    asname = self.any_to_str(ent.get("asname"))
                    line = "use " + base_path + "::" + name
                    if asname != "" and asname != name:
                        line += " as " + self._safe_name(asname)
                    _add(line + ";")
        return out

    def _infer_default_for_type(self, east_type: str) -> str:
        """型ごとの既定値（Rust）を返す。"""
        t = self.normalize_type_name(east_type)
        if self._is_any_type(t):
            self.uses_pyany = True
            return "PyAny::None"
        if t in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
            return "0"
        if t in {"float32", "float64"}:
            return "0.0"
        if t == "bool":
            return "false"
        if t == "str":
            return "String::new()"
        if t == "bytes" or t == "bytearray" or t.startswith("list["):
            return "Vec::new()"
        if t.startswith("set["):
            return "::std::collections::BTreeSet::new()"
        if t.startswith("dict["):
            return "::std::collections::BTreeMap::new()"
        if t.startswith("tuple["):
            return "()"
        if t == "None":
            return "()"
        if t.startswith("Option[") and t.endswith("]"):
            return "None"
        if t in self.class_names:
            return f"{t}::new()"
        return "Default::default()"

    def apply_cast(self, rendered_expr: str, to_type: str) -> str:
        """Rust 向けの最小キャストを適用する。"""
        t = self.normalize_type_name(to_type)
        if t == "":
            return rendered_expr
        rust_t = self._rust_type(t)
        if rust_t == "String":
            return self._ensure_string_owned(rendered_expr)
        if rust_t == "bool":
            return "((" + rendered_expr + ") != 0)"
        return "((" + rendered_expr + ") as " + rust_t + ")"

    def _refine_decl_type_from_value(self, declared_type: str, value_node: Any) -> str:
        """`Any` を含む宣言型より値側の具体型が有用なら値側を優先する。"""
        d = self.normalize_type_name(declared_type)
        if d == "":
            return self.get_expr_type(value_node)
        v = self.normalize_type_name(self.get_expr_type(value_node))
        if v == "":
            return d
        if self.is_any_like_type(d):
            return v
        if self._contains_text(d, "Any"):
            # `dict[str, Any]` などのコンテナ注釈は、Rust 側の型整合を優先して
            # 宣言型を保持する。値側推論で過度に具体化すると、混在値辞書が壊れる。
            if d.startswith("dict[") or d.startswith("list[") or d.startswith("tuple["):
                return d
            if d.startswith("dict[") and v.startswith("dict["):
                return v
            if d.startswith("list[") and v.startswith("list["):
                return v
            if d.startswith("tuple[") and v.startswith("tuple["):
                return v
        return d

    def _rust_type(self, east_type: str) -> str:
        """EAST 型名を Rust 型名へ変換する。"""
        t, mapped = self.normalize_type_and_lookup_map(east_type, self.type_map)
        if t == "":
            return "i64"
        if self._is_any_type(t):
            self.uses_pyany = True
            return "PyAny"
        if mapped != "":
            return mapped
        list_inner = self.type_generic_args(t, "list")
        if len(list_inner) == 1:
            return f"Vec<{self._rust_type(list_inner[0])}>"
        set_inner = self.type_generic_args(t, "set")
        if len(set_inner) == 1:
            return f"::std::collections::BTreeSet<{self._rust_type(set_inner[0])}>"
        dict_inner = self.type_generic_args(t, "dict")
        if len(dict_inner) == 2:
            parts = dict_inner
            return (
                "::std::collections::BTreeMap<"
                + self._rust_type(parts[0])
                + ", "
                + self._rust_type(parts[1])
                + ">"
            )
        tuple_inner = self.type_generic_args(t, "tuple")
        if len(tuple_inner) > 0:
            rendered: list[str] = []
            for part in tuple_inner:
                rendered.append(self._rust_type(part))
            if len(rendered) == 1:
                return f"({rendered[0]},)"
            return "(" + ", ".join(rendered) + ")"
        if t.find("|") >= 0:
            union_parts = self.split_union(t)
            if len(union_parts) >= 2:
                non_none, has_none = self.split_union_non_none(t)
                any_like = False
                for part in non_none:
                    if self._is_any_type(part):
                        any_like = True
                        break
                if any_like:
                    self.uses_pyany = True
                    return "PyAny"
                if has_none and len(non_none) == 1:
                    return f"Option<{self._rust_type(non_none[0])}>"
                if (not has_none) and len(non_none) == 1:
                    return self._rust_type(non_none[0])
                return "String"
        if t == "None":
            return "()"
        return t

    def _emit_runtime_support(self) -> None:
        """Rust 単体実行に必要な最小 runtime/module を埋め込む。"""
        for line in RUST_RUNTIME_SUPPORT.splitlines():
            self.emit(line)

    def transpile(self) -> str:
        """モジュール全体を Rust ソースへ変換する。"""
        self.lines = []
        self.scope_stack = [set()]
        self.declared_var_types = {}
        self.uses_pyany = self._doc_mentions_any(self.doc)
        self.uses_isinstance_runtime = self._doc_mentions_isinstance(self.doc)
        self.class_type_id_map = {}
        self.type_info_map = {}
        self.function_arg_ref_modes = {}
        self.class_method_arg_ref_modes = {}
        self.current_ref_vars = set()

        module = self.doc
        body = self._dict_stmt_list(module.get("body"))
        meta = self.any_to_dict_or_empty(module.get("meta"))
        self.class_names = set()
        self.class_base_map = self._collect_class_base_map(body)
        self.function_return_types = {}
        for stmt in body:
            kind = self.any_dict_get_str(stmt, "kind", "")
            if kind == "ClassDef":
                class_name = self.any_to_str(stmt.get("name"))
                if class_name != "":
                    self.class_names.add(class_name)
            if kind == "FunctionDef":
                fn_name = self.any_to_str(stmt.get("name"))
                ret_type = self.normalize_type_name(self.any_to_str(stmt.get("return_type")))
                if fn_name != "":
                    self.function_return_types[fn_name] = ret_type
                    self.function_arg_ref_modes[self._safe_name(fn_name)] = self._compute_function_arg_ref_modes(stmt)

        self.load_import_bindings_from_meta(meta)
        self.emit_module_leading_trivia()
        use_lines = self._collect_use_lines(body, meta)
        for line in use_lines:
            self.emit(line)
        if len(use_lines) > 0:
            self.emit("")
        self._emit_runtime_support()
        self.emit("")
        if self.uses_pyany:
            self._emit_pyany_runtime()
            self.emit("")
        if self.uses_isinstance_runtime:
            self._prepare_type_id_table()
            self._emit_isinstance_runtime_helpers()
            self.emit("")

        top_level_stmts: list[dict[str, Any]] = []
        for stmt in body:
            kind = self.any_dict_get_str(stmt, "kind", "")
            if kind == "Import" or kind == "ImportFrom":
                continue
            if kind == "FunctionDef":
                self.emit_leading_comments(stmt)
                self._emit_function(stmt, in_class=None)
                self.emit("")
                continue
            if kind == "ClassDef":
                self.emit_leading_comments(stmt)
                self._emit_class(stmt)
                self.emit("")
                continue
            top_level_stmts.append(stmt)

        main_guard_body = self._dict_stmt_list(module.get("main_guard_body"))
        should_emit_main = len(main_guard_body) > 0 or len(top_level_stmts) > 0
        if should_emit_main:
            self.emit("fn main() {")
            scope: set[str] = set()
            self.emit_scoped_stmt_list(top_level_stmts + main_guard_body, scope)
            self.emit("}")

        return "\n".join(self.lines) + ("\n" if len(self.lines) > 0 else "")

    def _emit_class(self, stmt: dict[str, Any]) -> None:
        """ClassDef を最小構成の `struct + impl` として出力する。"""
        class_name_raw = self.any_to_str(stmt.get("name"))
        class_name = self._safe_name(class_name_raw)
        field_types = self.any_to_dict_or_empty(stmt.get("field_types"))
        norm_field_types: dict[str, str] = {}
        for key, val in field_types.items():
            if isinstance(key, str):
                norm_field_types[key] = self.normalize_type_name(self.any_to_str(val))
        self.class_field_types[class_name_raw] = norm_field_types

        self.emit("#[derive(Clone, Debug)]")
        if len(norm_field_types) == 0:
            self.emit(f"struct {class_name};")
        else:
            self.emit(f"struct {class_name} {{")
            self.indent += 1
            for name, t in norm_field_types.items():
                self.emit(f"{self._safe_name(name)}: {self._rust_type(t)},")
            self.indent -= 1
            self.emit("}")

        self.emit(f"impl {class_name} {{")
        self.indent += 1
        if class_name_raw in self.class_type_id_map:
            self.emit(f"const PYTRA_TYPE_ID: i64 = {self.class_type_id_map[class_name_raw]};")
            self.emit("")
        members = self._dict_stmt_list(stmt.get("body"))
        method_mut_map = self._analyze_class_method_mutability(members)
        self.class_method_mutability[class_name_raw] = method_mut_map
        self.class_method_mutability[class_name] = method_mut_map
        method_ref_modes: dict[str, list[bool]] = {}
        for member in members:
            if self.any_dict_get_str(member, "kind", "") != "FunctionDef":
                continue
            name = self.any_to_str(member.get("name"))
            if name == "__init__":
                continue
            method_ref_modes[self._safe_name(name)] = self._compute_function_arg_ref_modes(member, for_method=True)
        self.class_method_arg_ref_modes[class_name_raw] = method_ref_modes
        self.class_method_arg_ref_modes[class_name] = method_ref_modes
        self._emit_constructor(class_name, stmt, norm_field_types)
        for member in members:
            if self.any_dict_get_str(member, "kind", "") != "FunctionDef":
                continue
            name = self.any_to_str(member.get("name"))
            if name == "__init__":
                continue
            self.emit("")
            self._emit_function(member, in_class=class_name)
        self.indent -= 1
        self.emit("}")
        if self.uses_isinstance_runtime and class_name_raw in self.class_type_id_map:
            self.emit("")
            self.emit(f"impl PyRuntimeTypeId for {class_name} {{")
            self.indent += 1
            self.emit("fn py_runtime_type_id(&self) -> i64 {")
            self.indent += 1
            self.emit(f"{class_name}::PYTRA_TYPE_ID")
            self.indent -= 1
            self.emit("}")
            self.indent -= 1
            self.emit("}")

    def _emit_constructor(self, class_name: str, cls: dict[str, Any], field_types: dict[str, str]) -> None:
        """`__init__` から `new` を生成する。"""
        init_fn: dict[str, Any] | None = None
        body = self._dict_stmt_list(cls.get("body"))
        for member in body:
            if self.any_dict_get_str(member, "kind", "") == "FunctionDef" and self.any_to_str(member.get("name")) == "__init__":
                init_fn = member
                break

        arg_items: list[str] = []
        init_scope: set[str] = set()
        if init_fn is not None:
            arg_order = self.any_to_str_list(init_fn.get("arg_order"))
            arg_types = self.any_to_dict_or_empty(init_fn.get("arg_types"))
            for arg_name in arg_order:
                if arg_name == "self":
                    continue
                arg_type = self._rust_type(self.any_to_str(arg_types.get(arg_name)))
                safe = self._safe_name(arg_name)
                arg_items.append(f"{safe}: {arg_type}")
                init_scope.add(arg_name)
        elif len(field_types) > 0:
            for field_name, field_t in field_types.items():
                safe = self._safe_name(field_name)
                arg_items.append(f"{safe}: {self._rust_type(field_t)}")
                init_scope.add(field_name)

        args_text = ", ".join(arg_items)
        self.emit(f"fn new({args_text}) -> Self {{")
        self.indent += 1

        field_values: dict[str, str] = {}
        for field_name, field_t in field_types.items():
            field_values[field_name] = self._infer_default_for_type(field_t)

        if init_fn is not None:
            init_body = self._dict_stmt_list(init_fn.get("body"))
            for stmt in init_body:
                kind = self.any_dict_get_str(stmt, "kind", "")
                if kind != "Assign" and kind != "AnnAssign":
                    continue
                target = self.any_to_dict_or_empty(stmt.get("target"))
                if len(target) == 0:
                    targets = self._dict_stmt_list(stmt.get("targets"))
                    if len(targets) > 0:
                        target = targets[0]
                if self.any_dict_get_str(target, "kind", "") != "Attribute":
                    continue
                owner = self.any_to_dict_or_empty(target.get("value"))
                if self.any_dict_get_str(owner, "kind", "") != "Name":
                    continue
                if self.any_to_str(owner.get("id")) != "self":
                    continue
                field_name = self.any_to_str(target.get("attr"))
                if field_name == "":
                    continue
                value_node = stmt.get("value")
                if value_node is None:
                    continue
                if self._expr_mentions_name(value_node, "self"):
                    continue
                field_values[field_name] = self.render_expr(value_node)
        elif len(field_types) > 0:
            for field_name in field_types.keys():
                field_values[field_name] = self._safe_name(field_name)

        if len(field_types) == 0:
            if len(init_scope) > 0:
                args_names: list[str] = []
                for arg_name in init_scope:
                    args_names.append(self._safe_name(arg_name))
                self.emit("let _ = (" + ", ".join(args_names) + ");")
            self.emit("Self")
        else:
            self.emit("Self {")
            self.indent += 1
            for field_name in field_types.keys():
                safe = self._safe_name(field_name)
                self.emit(f"{safe}: {field_values.get(field_name, 'Default::default()')},")
            self.indent -= 1
            self.emit("}")

        self.indent -= 1
        self.emit("}")

    def _emit_function(self, fn: dict[str, Any], in_class: str | None) -> None:
        """FunctionDef を Rust 関数として出力する。"""
        fn_name_raw = self.any_to_str(fn.get("name"))
        fn_name = self._safe_name(fn_name_raw)
        arg_order = self.any_to_str_list(fn.get("arg_order"))
        arg_types = self.any_to_dict_or_empty(fn.get("arg_types"))
        arg_usage = self.any_to_dict_or_empty(fn.get("arg_usage"))
        body = self._dict_stmt_list(fn.get("body"))
        prev_write_counts = self.current_fn_write_counts
        prev_mut_call_counts = self.current_fn_mutating_call_counts
        prev_ref_vars = self.current_ref_vars
        self.current_fn_write_counts = self._collect_name_write_counts(body)
        self.current_fn_mutating_call_counts = self._collect_mutating_receiver_name_counts(body)
        self.current_ref_vars = set()
        args_text_list: list[str] = []
        scope_names: set[str] = set()
        if in_class is None:
            fn_ref_modes = self.function_arg_ref_modes.get(fn_name, [])
        else:
            fn_ref_modes = self.class_method_arg_ref_modes.get(in_class, {}).get(fn_name, [])
        arg_pos = 0

        if in_class is not None:
            if len(arg_order) > 0 and arg_order[0] == "self":
                self_write_count = self.current_fn_write_counts.get("self", 0)
                self_mut_call_count = self.current_fn_mutating_call_counts.get("self", 0)
                method_mut_map = self.class_method_mutability.get(in_class, {})
                self_mut_call_count += self._count_self_calls_to_mut_methods(body, method_mut_map)
                self_ref = "&mut self" if (self_write_count > 0 or self_mut_call_count > 0) else "&self"
                args_text_list.append(self_ref)
                scope_names.add("self")
                arg_order = arg_order[1:]

        for arg_name in arg_order:
            safe = self._safe_name(arg_name)
            arg_east_t = self.any_to_str(arg_types.get(arg_name))
            arg_t = self._rust_type(arg_east_t)
            usage = self.any_to_str(arg_usage.get(arg_name))
            write_count = self.current_fn_write_counts.get(arg_name, 0)
            mut_call_count = self.current_fn_mutating_call_counts.get(arg_name, 0)
            is_mut = usage == "reassigned" or usage == "mutable" or usage == "write" or write_count > 0 or mut_call_count > 0
            pass_by_ref = False
            if arg_pos < len(fn_ref_modes):
                pass_by_ref = fn_ref_modes[arg_pos]
            arg_pos += 1
            if pass_by_ref:
                if self.normalize_type_name(arg_east_t) == "str":
                    arg_t = "&str"
                else:
                    arg_t = "&" + arg_t
            prefix = "mut " if is_mut else ""
            args_text_list.append(f"{prefix}{safe}: {arg_t}")
            scope_names.add(arg_name)
            if pass_by_ref:
                self.current_ref_vars.add(arg_name)
            self.declared_var_types[arg_name] = self.normalize_type_name(self.any_to_str(arg_types.get(arg_name)))

        ret_t_east = self.normalize_type_name(self.any_to_str(fn.get("return_type")))
        ret_t = self._rust_type(ret_t_east)
        ret_txt = ""
        if ret_t != "()":
            ret_txt = " -> " + ret_t
        line = self.syntax_line(
            "function_open",
            "fn {name}({args}){ret_txt} {",
            {"name": fn_name, "args": ", ".join(args_text_list), "ret_txt": ret_txt},
        )
        self.emit(line)

        self.emit_scoped_stmt_list(body, scope_names)
        self.emit("}")
        self.current_fn_write_counts = prev_write_counts
        self.current_fn_mutating_call_counts = prev_mut_call_counts
        self.current_ref_vars = prev_ref_vars

    def emit_stmt(self, stmt: dict[str, Any]) -> None:
        """文ノードを Rust へ出力する。"""
        self.emit_leading_comments(stmt)
        hooked = self.hook_on_emit_stmt(stmt)
        if hooked is True:
            return
        kind = self.any_dict_get_str(stmt, "kind", "")
        hooked_kind = self.hook_on_emit_stmt_kind(kind, stmt)
        if hooked_kind is True:
            return

        if kind == "Pass":
            self.emit(self.syntax_text("pass_stmt", "// pass"))
            return
        if kind == "Break":
            self.emit(self.syntax_text("break_stmt", "break;"))
            return
        if kind == "Continue":
            self.emit(self.syntax_text("continue_stmt", "continue;"))
            return
        if kind == "Expr":
            expr_d = self.any_to_dict_or_empty(stmt.get("value"))
            if self.any_dict_get_str(expr_d, "kind", "") == "Name":
                expr_name = self.any_dict_get_str(expr_d, "id", "")
                if expr_name == "break":
                    self.emit(self.syntax_text("break_stmt", "break;"))
                    return
                if expr_name == "continue":
                    self.emit(self.syntax_text("continue_stmt", "continue;"))
                    return
                if expr_name == "pass":
                    self.emit(self.syntax_text("pass_stmt", "// pass"))
                    return
            expr_txt = self.render_expr(stmt.get("value"))
            self.emit(self.syntax_line("expr_stmt", "{expr};", {"expr": expr_txt}))
            return
        if kind == "Return":
            if stmt.get("value") is None:
                self.emit(self.syntax_text("return_void", "return;"))
            else:
                val = self.render_expr(stmt.get("value"))
                self.emit(self.syntax_line("return_value", "return {value};", {"value": val}))
            return
        if kind == "AnnAssign":
            self._emit_annassign(stmt)
            return
        if kind == "Assign":
            self._emit_assign(stmt)
            return
        if kind == "AugAssign":
            self._emit_augassign(stmt)
            return
        if kind == "Raise":
            exc_node = self.any_to_dict_or_empty(stmt.get("exc"))
            msg_expr = "\"runtime error\".to_string()"
            if self.any_dict_get_str(exc_node, "kind", "") == "Call":
                args = self.any_to_list(exc_node.get("args"))
                if len(args) > 0:
                    msg_expr = self.render_expr(args[0])
            elif len(exc_node) > 0:
                msg_expr = self.render_expr(exc_node)
            self.emit("panic!(\"{}\", " + msg_expr + ");")
            return
        if kind == "If":
            self._emit_if(stmt)
            return
        if kind == "While":
            self._emit_while(stmt)
            return
        if kind == "ForRange":
            self._emit_for_range(stmt)
            return
        if kind == "For":
            self._emit_for(stmt)
            return
        if kind == "Import" or kind == "ImportFrom":
            return

        # 未対応文はコメント化して処理継続する。
        self.emit("// unsupported stmt: " + kind)

    def _emit_if(self, stmt: dict[str, Any]) -> None:
        cond = self.render_cond(stmt.get("test"))
        self.emit_if_stmt_skeleton(
            cond,
            self._dict_stmt_list(stmt.get("body")),
            self._dict_stmt_list(stmt.get("orelse")),
            if_open_default="if {cond} {",
            else_open_default="} else {",
        )

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        cond = self.render_cond(stmt.get("test"))
        self.emit_while_stmt_skeleton(
            cond,
            self._dict_stmt_list(stmt.get("body")),
            while_open_default="while {cond} {",
        )

    def _emit_for_range(self, stmt: dict[str, Any]) -> None:
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        target = self._safe_name(self.any_dict_get_str(target_node, "id", "_i"))
        target_type = self._rust_type(self.any_to_str(stmt.get("target_type")))
        start = self.render_expr(stmt.get("start"))
        stop = self.render_expr(stmt.get("stop"))
        step = self.render_expr(stmt.get("step"))
        range_mode = self.any_to_str(stmt.get("range_mode"))

        self.emit(f"let mut {target}: {target_type} = {start};")
        cond = f"{target} < {stop}"
        if range_mode == "descending":
            cond = f"{target} > {stop}"
        body_scope: set[str] = set()
        body_scope.add(self.any_dict_get_str(target_node, "id", target))
        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_block_with_tail_lines(
            self.syntax_line("for_range_open", "while {cond} {", {"cond": cond}),
            body,
            body_scope,
            [f"{target} += {step};"],
        )

    def _emit_for(self, stmt: dict[str, Any]) -> None:
        target_node = self.any_to_dict_or_empty(stmt.get("target"))
        target_name = self.any_dict_get_str(target_node, "id", "_it")
        target = self._safe_name(target_name)
        body_scope: set[str] = set()
        target_kind = self.any_dict_get_str(target_node, "kind", "")
        if target_kind == "Name":
            body_scope.add(target_name)
        elif target_kind == "Tuple":
            elts = self.tuple_elements(target_node)
            parts: list[str] = []
            for elt in elts:
                d = self.any_to_dict_or_empty(elt)
                if self.any_dict_get_str(d, "kind", "") == "Name":
                    name = self.any_dict_get_str(d, "id", "_")
                    parts.append(self._safe_name(name))
                    body_scope.add(name)
                else:
                    parts.append("_")
            if len(parts) == 1:
                target = "(" + parts[0] + ",)"
            elif len(parts) > 1:
                target = "(" + ", ".join(parts) + ")"

        iter_node = stmt.get("iter")
        iter_d = self.any_to_dict_or_empty(iter_node)
        iter_expr = self.render_expr(iter_node)
        iter_type = self.get_expr_type(iter_node)
        iter_is_attr_view = False
        iter_is_enumerate_call = False
        if self.any_dict_get_str(iter_d, "kind", "") == "Call":
            fn_d = self.any_to_dict_or_empty(iter_d.get("func"))
            fn_kind = self.any_dict_get_str(fn_d, "kind", "")
            if fn_kind == "Attribute":
                attr_name = self.any_dict_get_str(fn_d, "attr", "")
                if attr_name == "items" or attr_name == "keys" or attr_name == "values":
                    iter_is_attr_view = True
            elif fn_kind == "Name":
                iter_is_enumerate_call = self.any_dict_get_str(fn_d, "id", "") == "enumerate"
        if iter_type == "" or iter_type == "unknown":
            iter_type = self._dict_items_owner_type(iter_node)
        iter_key_t = ""
        iter_val_t = ""
        if iter_type.startswith("dict["):
            iter_key_t, iter_val_t = self._dict_key_value_types(iter_type)
        if iter_type == "str":
            iter_expr = iter_expr + ".chars()"
        elif (
            iter_type.startswith("list[")
            or iter_type.startswith("set[")
            or iter_type.startswith("dict[")
        ) and (not iter_is_attr_view) and (not iter_is_enumerate_call):
            if iter_type.startswith("list["):
                iter_expr = self._render_list_iter_expr(iter_expr, iter_type, self._can_borrow_iter_node(iter_node))
            else:
                iter_expr = "(" + iter_expr + ").clone()"

        if target_kind == "Tuple":
            elts = self.tuple_elements(target_node)
            if len(elts) >= 2 and iter_key_t != "" and iter_val_t != "":
                k_node = self.any_to_dict_or_empty(elts[0])
                v_node = self.any_to_dict_or_empty(elts[1])
                if self.any_dict_get_str(k_node, "kind", "") == "Name":
                    self.declared_var_types[self.any_dict_get_str(k_node, "id", "")] = iter_key_t
                if self.any_dict_get_str(v_node, "kind", "") == "Name":
                    self.declared_var_types[self.any_dict_get_str(v_node, "id", "")] = iter_val_t

        body = self._dict_stmt_list(stmt.get("body"))
        self.emit_scoped_block(
            self.syntax_line("for_open", "for {target} in {iter} {", {"target": target, "iter": iter_expr}),
            body,
            body_scope,
        )

    def _render_as_pyany(self, expr: Any) -> str:
        """式を `PyAny` へ昇格する。"""
        expr_d = self.any_to_dict_or_empty(expr)
        kind = self.any_dict_get_str(expr_d, "kind", "")
        src_t = self.normalize_type_name(self.get_expr_type(expr))
        self.uses_pyany = True
        if src_t == "PyAny" or self._is_any_type(src_t):
            return self.render_expr(expr)
        if kind == "Dict":
            return "PyAny::Dict(" + self._render_dict_expr(expr_d, force_any_values=True) + ")"
        if kind == "List":
            items = self.any_to_list(expr_d.get("elts"))
            vals: list[str] = []
            for item in items:
                vals.append(self._render_as_pyany(item))
            return "PyAny::List(vec![" + ", ".join(vals) + "])"
        if kind == "Set":
            items = self.any_to_list(expr_d.get("elements"))
            if len(items) == 0:
                items = self.any_to_list(expr_d.get("elts"))
            vals: list[str] = []
            for item in items:
                vals.append(self._render_as_pyany(item))
            return "PyAny::Set(vec![" + ", ".join(vals) + "])"
        rendered = self.render_expr(expr)
        if self._is_int_type(src_t):
            return "PyAny::Int((" + rendered + ") as i64)"
        if self._is_float_type(src_t):
            return "PyAny::Float((" + rendered + ") as f64)"
        if src_t == "bool":
            return "PyAny::Bool(" + rendered + ")"
        if src_t == "str":
            return "PyAny::Str(" + self._ensure_string_owned(rendered) + ")"
        if src_t == "None":
            return "PyAny::None"
        return "PyAny::Str(format!(\"{:?}\", " + rendered + "))"

    def _render_dict_expr(self, expr_d: dict[str, Any], *, force_any_values: bool = False) -> str:
        """Dict リテラルを Rust `BTreeMap::from([...])` へ描画する。"""
        dict_t = self.normalize_type_name(self.get_expr_type(expr_d))
        key_t = ""
        val_t = ""
        if dict_t.startswith("dict[") and dict_t.endswith("]"):
            key_t, val_t = self._dict_key_value_types(dict_t)
        if force_any_values:
            val_t = "Any"

        pairs: list[str] = []
        entries = self.any_to_list(expr_d.get("entries"))
        if len(entries) > 0:
            i = 0
            while i < len(entries):
                ent = self.any_to_dict_or_empty(entries[i])
                key_node = ent.get("key")
                val_node = ent.get("value")
                key_txt = self.render_expr(key_node)
                if key_t == "str":
                    key_txt = self._ensure_string_owned(key_txt)
                val_txt = self.render_expr(val_node)
                if self._is_any_type(val_t):
                    val_txt = self._render_as_pyany(val_node)
                pairs.append("(" + key_txt + ", " + val_txt + ")")
                i += 1
        else:
            keys = self.any_to_list(expr_d.get("keys"))
            vals = self.any_to_list(expr_d.get("values"))
            i = 0
            while i < len(keys) and i < len(vals):
                key_node = keys[i]
                val_node = vals[i]
                key_txt = self.render_expr(key_node)
                if key_t == "str":
                    key_txt = self._ensure_string_owned(key_txt)
                val_txt = self.render_expr(val_node)
                if self._is_any_type(val_t):
                    val_txt = self._render_as_pyany(val_node)
                pairs.append("(" + key_txt + ", " + val_txt + ")")
                i += 1
        return "::std::collections::BTreeMap::from([" + ", ".join(pairs) + "])"

    def _render_value_for_decl_type(self, value_obj: Any, target_type: str) -> str:
        """宣言型に合わせて右辺式を補正する。"""
        t = self.normalize_type_name(target_type)
        value_d = self.any_to_dict_or_empty(value_obj)
        value_kind = self.any_dict_get_str(value_d, "kind", "")
        if self._is_any_type(t):
            return self._render_as_pyany(value_obj)
        if self._is_dict_with_any_value(t):
            if value_kind == "Dict":
                return self._render_dict_expr(value_d, force_any_values=True)
            rendered = self.render_expr(value_obj)
            src_t = self.normalize_type_name(self.get_expr_type(value_obj))
            if self._is_any_type(src_t):
                self.uses_pyany = True
                return "py_any_as_dict(" + rendered + ")"
            if value_kind == "Call":
                owner_val_t = self._dict_get_owner_value_type(value_obj)
                if self._is_any_type(owner_val_t):
                    self.uses_pyany = True
                    return "py_any_as_dict(" + rendered + ")"
            return rendered
        if t == "str":
            return self._ensure_string_owned(self.render_expr(value_obj))
        return self.render_expr(value_obj)

    def _infer_byte_buffer_capacity_expr(self, target_name_raw: str) -> str:
        """`bytearray()/bytes()` 初期化向けの容量式を推定する。"""
        name = target_name_raw.lower()
        width_name = ""
        height_name = ""
        if self.is_declared("width"):
            width_name = "width"
        elif self.is_declared("w"):
            width_name = "w"
        if self.is_declared("height"):
            height_name = "height"
        elif self.is_declared("h"):
            height_name = "h"

        if width_name != "" and height_name != "":
            w = self._safe_name(width_name)
            h = self._safe_name(height_name)
            area = "((" + w + ") * (" + h + "))"
            if "pixel" in name:
                return "(" + area + " * 3)"
            if "scanline" in name:
                return "((" + h + ") * (((" + w + ") * 3) + 1))"
            if "frame" in name:
                return area
            return area
        if "palette" in name:
            return "(256 * 3)"
        return ""

    def _maybe_render_preallocated_byte_buffer_init(self, target_name_raw: str, target_type: str, value_obj: Any) -> str:
        """空 `bytearray()/bytes()` 初期化で `with_capacity` を返す。"""
        t = self.normalize_type_name(target_type)
        if t not in {"bytearray", "bytes"}:
            return ""
        value_d = self.any_to_dict_or_empty(value_obj)
        if self.any_dict_get_str(value_d, "kind", "") != "Call":
            return ""
        fn_d = self.any_to_dict_or_empty(value_d.get("func"))
        if self.any_dict_get_str(fn_d, "kind", "") != "Name":
            return ""
        fn_name = self.any_dict_get_str(fn_d, "id", "")
        if fn_name != "bytearray" and fn_name != "bytes":
            return ""
        call_args = self.any_to_list(value_d.get("args"))
        call_kws = self.any_to_list(value_d.get("keywords"))
        call_kw_values = self.any_to_list(value_d.get("kw_values"))
        if len(call_args) != 0 or len(call_kws) != 0 or len(call_kw_values) != 0:
            return ""
        cap_expr = self._infer_byte_buffer_capacity_expr(target_name_raw)
        if cap_expr == "":
            return ""
        return "Vec::<u8>::with_capacity((" + cap_expr + ") as usize)"

    def _emit_annassign(self, stmt: dict[str, Any]) -> None:
        target = self.any_to_dict_or_empty(stmt.get("target"))
        target_kind = self.any_dict_get_str(target, "kind", "")
        if target_kind != "Name":
            t = self.render_expr(target)
            if target_kind == "Subscript":
                v = self.render_expr(stmt.get("value"))
                self._emit_subscript_set(target, v)
                return
            v = self.render_expr(stmt.get("value"))
            self.emit(self.syntax_line("annassign_assign", "{target} = {value};", {"target": t, "value": v}))
            return

        name_raw = self.any_dict_get_str(target, "id", "_")
        name = self._safe_name(name_raw)
        ann = self.any_to_str(stmt.get("annotation"))
        decl_t = self.any_to_str(stmt.get("decl_type"))
        t_east = ann if ann != "" else decl_t
        if t_east == "":
            t_east = self.get_expr_type(stmt.get("value"))
        else:
            t_east = self._refine_decl_type_from_value(t_east, stmt.get("value"))
        t = self._rust_type(t_east)
        self.declare_in_current_scope(name_raw)
        self.declared_var_types[name_raw] = self.normalize_type_name(t_east)

        value_obj = stmt.get("value")
        if value_obj is None:
            mut_kw = "mut " if self._should_declare_mut(name_raw, has_init_write=False) else ""
            self.emit(self.syntax_line("annassign_decl_noinit", "let {mut_kw}{target}: {type};", {"mut_kw": mut_kw, "target": name, "type": t}))
            return
        value = self._maybe_render_preallocated_byte_buffer_init(name_raw, t_east, value_obj)
        if value == "":
            value = self._render_value_for_decl_type(value_obj, t_east)
        mut_kw = "mut " if self._should_declare_mut(name_raw, has_init_write=True) else ""
        self.emit(
            self.syntax_line(
                "annassign_decl_init",
                "let {mut_kw}{target}: {type} = {value};",
                {"mut_kw": mut_kw, "target": name, "type": t, "value": value},
            )
        )

    def _emit_assign(self, stmt: dict[str, Any]) -> None:
        target = self.primary_assign_target(stmt)
        value = self.render_expr(stmt.get("value"))
        if self.any_dict_get_str(target, "kind", "") == "Name":
            name_raw = self.any_dict_get_str(target, "id", "_")
            name = self._safe_name(name_raw)
            if self.should_declare_name_binding(stmt, name_raw, False):
                self.declare_in_current_scope(name_raw)
                t = self.get_expr_type(stmt.get("value"))
                if t != "":
                    self.declared_var_types[name_raw] = t
                mut_kw = "mut " if self._should_declare_mut(name_raw, has_init_write=True) else ""
                prealloc_value = self._maybe_render_preallocated_byte_buffer_init(name_raw, t, stmt.get("value"))
                if prealloc_value != "":
                    value = prealloc_value
                self.emit(self.syntax_line("assign_decl_init", "let {mut_kw}{target} = {value};", {"mut_kw": mut_kw, "target": name, "value": value}))
                return
            self.emit(self.syntax_line("assign_set", "{target} = {value};", {"target": name, "value": value}))
            return

        if self._emit_tuple_assign(target, value):
            return

        rendered_target = self.render_expr(target)
        if self.any_dict_get_str(target, "kind", "") == "Subscript":
            owner_node = self.any_to_dict_or_empty(target.get("value"))
            owner_t = self.normalize_type_name(self.get_expr_type(owner_node))
            if owner_t in {"bytes", "bytearray"}:
                value = "((" + value + ") as u8)"
            self._emit_subscript_set(target, value)
            return
        self.emit(self.syntax_line("assign_set", "{target} = {value};", {"target": rendered_target, "value": value}))

    def _render_subscript_lvalue(self, subscript_expr: dict[str, Any]) -> str:
        """Subscript を代入先として描画する（clone を付けない）。"""
        owner = self.render_expr(subscript_expr.get("value"))
        idx = self.render_expr(subscript_expr.get("slice"))
        idx_i64 = "((" + idx + ") as i64)"
        idx_usize = "((if " + idx_i64 + " < 0 { (" + owner + ".len() as i64 + " + idx_i64 + ") } else { " + idx_i64 + " }) as usize)"
        return owner + "[" + idx_usize + "]"

    def _collect_subscript_chain(self, subscript_expr: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """`a[b][c]` を `(a, [a[b], a[b][c]])` 形式に分解する。"""
        chain: list[dict[str, Any]] = []
        cur = self.any_to_dict_or_empty(subscript_expr)
        while self.any_dict_get_str(cur, "kind", "") == "Subscript":
            chain.append(cur)
            cur = self.any_to_dict_or_empty(cur.get("value"))
        chain.reverse()
        return cur, chain

    def _emit_subscript_set(self, subscript_expr: dict[str, Any], value_expr: str) -> None:
        """Subscript 代入を borrow-safe な `let idx` 形式で出力する。"""
        owner_node = self.any_to_dict_or_empty(subscript_expr.get("value"))
        owner_t = self.normalize_type_name(self.get_expr_type(owner_node))
        if owner_t.startswith("dict["):
            key_t, _val_t = self._dict_key_value_types(owner_t)
            owner_expr = self.render_expr(owner_node)
            key_expr = self.render_expr(subscript_expr.get("slice"))
            key_expr = self._coerce_dict_key_expr(key_expr, key_t)
            self.emit(owner_expr + ".insert(" + key_expr + ", " + value_expr + ");")
            return

        base_node, chain = self._collect_subscript_chain(subscript_expr)
        if len(chain) == 0:
            self.emit(self._render_subscript_lvalue(subscript_expr) + " = " + value_expr + ";")
            return

        owner_expr = self.render_expr(base_node)
        i = 0
        while i < len(chain):
            level = self.any_to_dict_or_empty(chain[i])
            slice_node = self.any_to_dict_or_empty(level.get("slice"))
            if self.any_dict_get_str(slice_node, "kind", "") == "Slice":
                self.emit(self._render_subscript_lvalue(subscript_expr) + " = " + value_expr + ";")
                return
            idx_txt = self.render_expr(slice_node)
            idx_i64_tmp = self.next_tmp("__idx_i64")
            idx_tmp = self.next_tmp("__idx")
            self.emit("let " + idx_i64_tmp + " = ((" + idx_txt + ") as i64);")
            self.emit(
                "let "
                + idx_tmp
                + " = if "
                + idx_i64_tmp
                + " < 0 { ("
                + owner_expr
                + ".len() as i64 + "
                + idx_i64_tmp
                + ") as usize } else { "
                + idx_i64_tmp
                + " as usize };"
            )
            owner_expr = owner_expr + "[" + idx_tmp + "]"
            i += 1
        self.emit(owner_expr + " = " + value_expr + ";")

    def _emit_tuple_assign(self, target_node: dict[str, Any], value_expr: str) -> bool:
        """Tuple unpack 代入を `tmp.N` へ lower する（任意要素数対応）。"""
        if self.any_dict_get_str(target_node, "kind", "") != "Tuple":
            return False
        targets = self.tuple_elements(target_node)
        if len(targets) == 0:
            return False
        tmp_name = self.next_tmp("__tmp")
        self.emit("let " + tmp_name + " = " + value_expr + ";")
        i = 0
        while i < len(targets):
            elem = self.any_to_dict_or_empty(targets[i])
            item_expr = tmp_name + "." + str(i)
            elem_kind = self.any_dict_get_str(elem, "kind", "")
            if elem_kind == "Name":
                name_raw = self.any_dict_get_str(elem, "id", "")
                name = self._safe_name(name_raw)
                if name_raw != "" and not self.is_declared(name_raw):
                    self.declare_in_current_scope(name_raw)
                    mut_kw = "mut " if self._should_declare_mut(name_raw, has_init_write=True) else ""
                    self.emit("let " + mut_kw + name + " = " + item_expr + ";")
                else:
                    self.emit(name + " = " + item_expr + ";")
                i += 1
                continue
            if elem_kind == "Subscript":
                self._emit_subscript_set(elem, item_expr)
                i += 1
                continue
            self.emit(self.render_expr(elem) + " = " + item_expr + ";")
            i += 1
        return True

    def _emit_augassign(self, stmt: dict[str, Any]) -> None:
        target_obj = stmt.get("target")
        value_obj = stmt.get("value")
        target, value, mapped = self.render_augassign_basic(stmt, self.aug_ops, "+=")
        target_t = self.normalize_type_name(self.get_expr_type(target_obj))
        value_t = self.normalize_type_name(self.get_expr_type(value_obj))
        if self._is_any_type(value_t):
            self.uses_pyany = True
            if self._is_int_type(target_t):
                value = "py_any_to_i64(&" + value + ")"
            elif self._is_float_type(target_t):
                value = "py_any_to_f64(&" + value + ")"
            elif target_t == "bool":
                value = "py_any_to_bool(&" + value + ")"
            elif target_t == "str" and mapped == "+=":
                value = "py_any_to_string(&" + value + ")"
        self.emit(self.syntax_line("augassign_apply", "{target} {op} {value};", {"target": target, "op": mapped, "value": value}))

    def _collect_class_base_map(self, body: list[dict[str, Any]]) -> dict[str, str]:
        """ClassDef から `child -> base` の継承表を抽出する。"""
        out: dict[str, str] = {}
        for stmt in body:
            if self.any_dict_get_str(stmt, "kind", "") != "ClassDef":
                continue
            child = self.any_to_str(stmt.get("name"))
            if child == "":
                continue
            base = self.any_to_str(stmt.get("base"))
            if base != "":
                out[child] = self.normalize_type_name(base)
        return out

    def _is_class_subtype(self, actual: str, expected: str) -> bool:
        """`actual` が `expected` の派生型かを継承表で判定する。"""
        cur = self.normalize_type_name(actual)
        want = self.normalize_type_name(expected)
        if cur == "" or want == "":
            return False
        if cur == want:
            return True
        visited: set[str] = set()
        while cur != "" and cur not in visited:
            visited.add(cur)
            if cur == want:
                return True
            if cur not in self.class_base_map:
                break
            cur = self.normalize_type_name(self.class_base_map[cur])
        return False

    def _render_isinstance_type_check(self, value_expr: str, value_node: Any, type_name: str) -> str:
        """`isinstance(x, T)` の `T` を Rust 式へ lower する。"""
        expected_tid = self._builtin_type_id_expr(type_name)
        if expected_tid == "":
            return "false"
        actual = self.normalize_type_name(self.get_expr_type(value_node))
        if self._is_any_type(actual):
            self.uses_pyany = True
        self.uses_isinstance_runtime = True
        return "py_isinstance(&" + value_expr + ", " + expected_tid + ")"

    def _render_isinstance_call(self, rendered_args: list[str], arg_nodes: list[Any]) -> str:
        """`isinstance(...)` 呼び出しを Rust へ lower する。"""
        if len(rendered_args) != 2:
            return "false"
        rhs_node = self.any_to_dict_or_empty(arg_nodes[1] if len(arg_nodes) > 1 else None)
        rhs_kind = self.any_dict_get_str(rhs_node, "kind", "")
        if rhs_kind == "Name":
            rhs_name = self.any_dict_get_str(rhs_node, "id", "")
            lowered = self._render_isinstance_type_check(rendered_args[0], arg_nodes[0] if len(arg_nodes) > 0 else None, rhs_name)
            if lowered != "":
                return lowered
            return "false"
        if rhs_kind == "Tuple":
            checks: list[str] = []
            for elt in self.tuple_elements(rhs_node):
                e_node = self.any_to_dict_or_empty(elt)
                if self.any_dict_get_str(e_node, "kind", "") != "Name":
                    continue
                e_name = self.any_dict_get_str(e_node, "id", "")
                lowered = self._render_isinstance_type_check(rendered_args[0], arg_nodes[0] if len(arg_nodes) > 0 else None, e_name)
                if lowered != "":
                    checks.append(lowered)
            if len(checks) > 0:
                return "(" + " || ".join(checks) + ")"
        return "false"

    def _render_compare(self, expr: dict[str, Any]) -> str:
        left_node = self.any_to_dict_or_empty(expr.get("left"))
        left = self.render_expr(left_node)
        ops = self.any_to_str_list(expr.get("ops"))
        comps = self.any_to_list(expr.get("comparators"))
        if len(ops) == 0 or len(comps) == 0:
            return "false"
        terms: list[str] = []
        cur_left_node = left_node
        cur_left = left
        pair_count = len(ops)
        if len(comps) < pair_count:
            pair_count = len(comps)
        i = 0
        while i < pair_count:
            right_node = self.any_to_dict_or_empty(comps[i])
            right = self.render_expr(right_node)
            op = ops[i]
            if op == "In" or op == "NotIn":
                terms.append("(" + self._render_membership_compare_term(op, cur_left, cur_left_node, right, right_node) + ")")
            else:
                mapped = self.cmp_ops.get(op, "==")
                cmp_left = cur_left
                cmp_right = right
                if mapped in {"==", "!="}:
                    lit_right = self._string_constant_literal(right_node)
                    lit_left = self._string_constant_literal(cur_left_node)
                    if lit_right != "":
                        cmp_right = lit_right
                    if lit_left != "":
                        cmp_left = lit_left
                terms.append("(" + cmp_left + " " + mapped + " " + cmp_right + ")")
            cur_left_node = right_node
            cur_left = right
            i += 1
        if len(terms) == 0:
            return "false"
        if len(terms) == 1:
            return terms[0]
        return "(" + " && ".join(terms) + ")"

    def _render_membership_compare_term(
        self,
        op: str,
        left_expr: str,
        left_node: dict[str, Any],
        right_expr: str,
        right_node: dict[str, Any],
    ) -> str:
        """`in` / `not in` を owner 型に応じて lower する。"""
        right_t = self.normalize_type_name(self.get_expr_type(right_node))
        left_t = self.normalize_type_name(self.get_expr_type(left_node))
        term = left_expr + " == " + right_expr
        if right_t.startswith("dict["):
            key_t, _val_t = self._dict_key_value_types(right_t)
            key_expr = self._coerce_dict_key_expr(left_expr, key_t, require_owned=False)
            term = right_expr + ".contains_key(&" + key_expr + ")"
        elif right_t == "str":
            if left_t == "str":
                term = right_expr + ".contains(&(" + left_expr + "))"
            else:
                term = right_expr + ".contains(&(" + left_expr + ").to_string())"
        elif (
            right_t.startswith("list[")
            or right_t.startswith("tuple[")
            or right_t.startswith("set[")
            or right_t in {"bytes", "bytearray"}
        ):
            term = right_expr + ".contains(&(" + left_expr + "))"
        if op == "NotIn":
            return "!(" + term + ")"
        return term

    def _render_ifexp_expr(self, expr: dict[str, Any]) -> str:
        """IfExp を Rust if 式へ描画する。"""
        body = self.render_expr(expr.get("body"))
        orelse = self.render_expr(expr.get("orelse"))
        casts = self._dict_stmt_list(expr.get("casts"))
        for cast_info in casts:
            on = self.any_to_str(cast_info.get("on"))
            to_t = self.any_to_str(cast_info.get("to"))
            if on == "body":
                body = self.apply_cast(body, to_t)
            elif on == "orelse":
                orelse = self.apply_cast(orelse, to_t)
        test_expr = self.render_cond(expr.get("test"))
        return self.render_ifexp_common(
            test_expr,
            body,
            orelse,
            test_node=self.any_to_dict_or_empty(expr.get("test")),
            fold_bool_literal=True,
        )

    def render_ifexp_common(
        self,
        test_expr: str,
        body_expr: str,
        orelse_expr: str,
        *,
        test_node: dict[str, Any] | None = None,
        fold_bool_literal: bool = False,
    ) -> str:
        """Rust の if 式として IfExp を描画する。"""
        if fold_bool_literal:
            node = test_node if isinstance(test_node, dict) else {}
            if self._node_kind_from_dict(node) == "Constant" and isinstance(node.get("value"), bool):
                return body_expr if bool(node.get("value")) else orelse_expr
            if self._node_kind_from_dict(node) == "Name":
                ident = self.any_to_str(node.get("id"))
                if ident == "True":
                    return body_expr
                if ident == "False":
                    return orelse_expr
            t = test_expr.strip()
            if t == "true":
                return body_expr
            if t == "false":
                return orelse_expr
        return "(if " + test_expr + " { " + body_expr + " } else { " + orelse_expr + " })"

    def _render_range_expr(self, expr_d: dict[str, Any]) -> str:
        """RangeExpr を Rust range 式へ描画する。"""
        start = self.render_expr(expr_d.get("start"))
        stop = self.render_expr(expr_d.get("stop"))
        step = self.render_expr(expr_d.get("step"))
        if step == "1":
            return "((" + start + ")..(" + stop + "))"
        return "((" + start + ")..(" + stop + ")).step_by(((" + step + ") as usize))"

    def _render_list_comp(self, expr_d: dict[str, Any]) -> str:
        """最小限の ListComp（単一 generator）を Rust へ描画する。"""
        generators = self.any_to_list(expr_d.get("generators"))
        if len(generators) != 1:
            return "vec![]"
        gen = self.any_to_dict_or_empty(generators[0])
        if len(self.any_to_list(gen.get("ifs"))) > 0:
            return "vec![]"
        target_node = self.any_to_dict_or_empty(gen.get("target"))
        target_kind = self.any_dict_get_str(target_node, "kind", "")
        if target_kind != "Name":
            return "vec![]"
        target_name = self._safe_name(self.any_dict_get_str(target_node, "id", "_item"))
        iter_node = self.any_to_dict_or_empty(gen.get("iter"))
        iter_expr = self.render_expr(iter_node)
        if self.any_dict_get_str(iter_node, "kind", "") == "RangeExpr":
            iter_expr = self._render_range_expr(iter_node)
        elt_expr = self.render_expr(expr_d.get("elt"))
        return "(" + iter_expr + ").map(|" + target_name + "| " + elt_expr + ").collect::<Vec<_>>()"

    def _render_binop(self, expr: dict[str, Any]) -> str:
        op = self.any_to_str(expr.get("op"))
        left_node = self.any_to_dict_or_empty(expr.get("left"))
        right_node = self.any_to_dict_or_empty(expr.get("right"))
        left_t = self.normalize_type_name(self.get_expr_type(left_node))
        right_t = self.normalize_type_name(self.get_expr_type(right_node))
        if op == "Mult":
            left_kind = self.any_dict_get_str(left_node, "kind", "")
            right_kind = self.any_dict_get_str(right_node, "kind", "")
            if left_kind == "List":
                left_items = self.any_to_list(left_node.get("elts"))
                if len(left_items) == 0:
                    left_items = self.any_to_list(left_node.get("elements"))
                if len(left_items) == 1:
                    item_txt = self.render_expr(left_items[0])
                    repeat_txt = self.render_expr(right_node)
                    return "vec![" + item_txt + "; ((" + repeat_txt + ") as usize)]"
            if right_kind == "List":
                right_items = self.any_to_list(right_node.get("elts"))
                if len(right_items) == 0:
                    right_items = self.any_to_list(right_node.get("elements"))
                if len(right_items) == 1:
                    item_txt = self.render_expr(right_items[0])
                    repeat_txt = self.render_expr(left_node)
                    return "vec![" + item_txt + "; ((" + repeat_txt + ") as usize)]"
        left = self._wrap_for_binop_operand(self.render_expr(left_node), left_node, self.any_dict_get_str(expr, "op", ""), is_right=False)
        right = self._wrap_for_binop_operand(self.render_expr(right_node), right_node, self.any_dict_get_str(expr, "op", ""), is_right=True)
        casts = self._dict_stmt_list(expr.get("casts"))
        for cast_info in casts:
            on = self.any_to_str(cast_info.get("on"))
            to_t = self.any_to_str(cast_info.get("to"))
            if on == "left":
                left = self.apply_cast(left, to_t)
                if self.normalize_type_name(to_t) == "str":
                    left_t = "str"
            elif on == "right":
                right = self.apply_cast(right, to_t)
                if self.normalize_type_name(to_t) == "str":
                    right_t = "str"
        if op == "Add" and (left_t == "str" or right_t == "str"):
            return "format!(\"{}{}\", " + left + ", " + right + ")"
        custom = self.hook_on_render_binop(expr, left, right)
        if custom != "":
            return custom
        mapped = self.bin_ops.get(op, "+")
        return left + " " + mapped + " " + right

    def _should_clone_call_arg_type(self, arg_type: str) -> bool:
        t = self.normalize_type_name(arg_type)
        if t in {"bytes", "bytearray"}:
            return True
        if t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple["):
            return True
        if t in self.class_names:
            return True
        return False

    def _infer_expr_type_for_call_arg(self, node: Any) -> str:
        t = self.normalize_type_name(self.get_expr_type(node))
        if t != "" and t != "unknown":
            return t
        d = self.any_to_dict_or_empty(node)
        if self.any_dict_get_str(d, "kind", "") == "Attribute":
            owner = self.any_to_dict_or_empty(d.get("value"))
            owner_t = self.normalize_type_name(self.get_expr_type(owner))
            attr = self.any_dict_get_str(d, "attr", "")
            field_types = self.class_field_types.get(owner_t, {})
            if attr in field_types:
                return self.normalize_type_name(field_types[attr])
        return t

    def _clone_owned_call_args(self, rendered_args: list[str], arg_nodes: list[Any]) -> list[str]:
        out = list(rendered_args)
        i = 0
        while i < len(arg_nodes) and i < len(out):
            t = self._infer_expr_type_for_call_arg(arg_nodes[i])
            if self._should_clone_call_arg_type(t):
                out[i] = "(" + out[i] + ").clone()"
            i += 1
        return out

    def _render_by_ref_call_arg(self, arg_txt: str, arg_node: Any) -> str:
        """`&T` / `&str` 引数向けに最小コストの渡し方を選ぶ。"""
        str_lit = self._string_constant_literal(arg_node)
        if str_lit != "":
            return str_lit
        arg_d = self.any_to_dict_or_empty(arg_node)
        if self.any_dict_get_str(arg_d, "kind", "") == "Name":
            raw = self.any_dict_get_str(arg_d, "id", "")
            if raw in self.current_ref_vars:
                return arg_txt
        if arg_txt.startswith("&"):
            return arg_txt
        return "&(" + arg_txt + ")"

    def _render_call(self, expr: dict[str, Any]) -> str:
        parts = self.prepare_call_context(expr)
        fn_node = self.any_to_dict_or_empty(parts.get("fn"))
        fn_kind = self.any_dict_get_str(fn_node, "kind", "")
        args = self.any_to_list(parts.get("args"))
        arg_nodes = self.any_to_list(parts.get("arg_nodes"))
        kw_values = self.any_to_list(parts.get("kw_values"))

        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(self.any_to_str(args[i]))
            i += 1
        rendered_kw_values: list[str] = []
        j = 0
        while j < len(kw_values):
            rendered_kw_values.append(self.any_to_str(kw_values[j]))
            j += 1
        merged_args = self.merge_call_kw_values(rendered_args, rendered_kw_values)

        if fn_kind == "Name":
            fn_name_raw = self.any_dict_get_str(fn_node, "id", "")
            fn_name = self._safe_name(fn_name_raw)
            if fn_name_raw in self.class_names:
                ctor_args = self._clone_owned_call_args(merged_args, arg_nodes)
                field_types = self.class_field_types.get(fn_name_raw, {})
                if len(field_types) == len(ctor_args):
                    coerced: list[str] = []
                    idx = 0
                    for _field_name, field_t in field_types.items():
                        if idx >= len(ctor_args):
                            break
                        arg_txt = ctor_args[idx]
                        if self.normalize_type_name(field_t) == "str":
                            arg_txt = self._ensure_string_owned(arg_txt)
                        coerced.append(arg_txt)
                        idx += 1
                    if len(coerced) == len(ctor_args):
                        ctor_args = coerced
                return f"{self._safe_name(fn_name_raw)}::new(" + ", ".join(ctor_args) + ")"
            if fn_name_raw == "isinstance":
                return self._render_isinstance_call(rendered_args, arg_nodes)
            if fn_name_raw == "enumerate" and len(merged_args) == 1:
                arg_node = arg_nodes[0] if len(arg_nodes) > 0 else None
                arg_t = self.normalize_type_name(self.get_expr_type(arg_node))
                if arg_t.startswith("list["):
                    iter_expr = self._render_list_iter_expr(
                        merged_args[0], arg_t, self._can_borrow_iter_node(arg_node)
                    )
                    return iter_expr + ".enumerate().map(|(i, v)| (i as i64, v))"
                return "(" + merged_args[0] + ").clone().into_iter().enumerate().map(|(i, v)| (i as i64, v))"
            if fn_name_raw == "bytearray":
                if len(merged_args) == 0:
                    return "Vec::<u8>::new()"
                if len(merged_args) == 1:
                    arg0_node = arg_nodes[0] if len(arg_nodes) > 0 else None
                    arg0_t = self.normalize_type_name(self.get_expr_type(arg0_node))
                    if self._is_int_type(arg0_t):
                        return "vec![0u8; (" + merged_args[0] + ") as usize]"
                    if arg0_t == "bytes" or arg0_t == "bytearray" or arg0_t.startswith("list["):
                        return "(" + merged_args[0] + ").clone()"
                    return "(" + merged_args[0] + ").into_iter().map(|v| v as u8).collect::<Vec<u8>>()"
                return "Vec::<u8>::new()"
            if fn_name_raw == "bytes":
                if len(merged_args) == 0:
                    return "Vec::<u8>::new()"
                arg0_node = arg_nodes[0] if len(arg_nodes) > 0 else None
                arg0_t = self.normalize_type_name(self.get_expr_type(arg0_node))
                if arg0_t == "str":
                    return "(" + merged_args[0] + ").as_bytes().to_vec()"
                return "(" + merged_args[0] + ").clone()"
            if fn_name_raw == "print":
                if len(merged_args) == 0:
                    return "println!(\"\")"
                if len(merged_args) == 1:
                    return "println!(\"{}\", " + merged_args[0] + ")"
                placeholders: list[str] = []
                for _ in merged_args:
                    placeholders.append("{}")
                return "println!(\"" + " ".join(placeholders) + "\", " + ", ".join(merged_args) + ")"
            if fn_name_raw == "len" and len(merged_args) == 1:
                arg_type = self.get_expr_type(arg_nodes[0] if len(arg_nodes) > 0 else None)
                if arg_type.startswith("dict["):
                    return merged_args[0] + ".len() as i64"
                return merged_args[0] + ".len() as i64"
            if fn_name_raw == "max" and len(merged_args) >= 2:
                expr_txt = merged_args[0]
                k = 1
                while k < len(merged_args):
                    rhs = merged_args[k]
                    expr_txt = "(if " + expr_txt + " > " + rhs + " { " + expr_txt + " } else { " + rhs + " })"
                    k += 1
                return expr_txt
            if fn_name_raw == "min" and len(merged_args) >= 2:
                expr_txt = merged_args[0]
                k = 1
                while k < len(merged_args):
                    rhs = merged_args[k]
                    expr_txt = "(if " + expr_txt + " < " + rhs + " { " + expr_txt + " } else { " + rhs + " })"
                    k += 1
                return expr_txt
            if fn_name_raw == "str" and len(merged_args) == 1:
                arg_t = self.normalize_type_name(self.get_expr_type(arg_nodes[0] if len(arg_nodes) > 0 else None))
                arg_any = self._is_any_type(arg_t)
                if not arg_any and len(arg_nodes) > 0 and (arg_t == "" or arg_t == "unknown"):
                    arg_any = self._is_any_type(self._dict_get_owner_value_type(arg_nodes[0]))
                if arg_any:
                    self.uses_pyany = True
                    return "py_any_to_string(&" + merged_args[0] + ")"
                return "(" + merged_args[0] + ").to_string()"
            if fn_name_raw == "int" and len(merged_args) == 1:
                arg_node = arg_nodes[0] if len(arg_nodes) > 0 else None
                arg_t = self.normalize_type_name(self.get_expr_type(arg_node))
                if (arg_t == "" or arg_t == "unknown") and len(arg_nodes) > 0:
                    arg_d = self.any_to_dict_or_empty(arg_node)
                    if self.any_dict_get_str(arg_d, "kind", "") == "Attribute":
                        owner_node = self.any_to_dict_or_empty(arg_d.get("value"))
                        owner_t = self.normalize_type_name(self.get_expr_type(owner_node))
                        attr_name = self.any_dict_get_str(arg_d, "attr", "")
                        field_types = self.class_field_types.get(owner_t, {})
                        if attr_name in field_types:
                            arg_t = self.normalize_type_name(field_types[attr_name])
                arg_any = self._is_any_type(arg_t)
                if not arg_any and len(arg_nodes) > 0 and (arg_t == "" or arg_t == "unknown"):
                    arg_any = self._is_any_type(self._dict_get_owner_value_type(arg_nodes[0]))
                if arg_any:
                    self.uses_pyany = True
                    return "py_any_to_i64(&" + merged_args[0] + ")"
                if arg_t == "str":
                    return "((" + merged_args[0] + ").parse::<i64>().unwrap_or(0))"
                return "((" + merged_args[0] + ") as i64)"
            if fn_name_raw == "float" and len(merged_args) == 1:
                arg_t = self.normalize_type_name(self.get_expr_type(arg_nodes[0] if len(arg_nodes) > 0 else None))
                arg_any = self._is_any_type(arg_t)
                if not arg_any and len(arg_nodes) > 0 and (arg_t == "" or arg_t == "unknown"):
                    arg_any = self._is_any_type(self._dict_get_owner_value_type(arg_nodes[0]))
                if arg_any:
                    self.uses_pyany = True
                    return "py_any_to_f64(&" + merged_args[0] + ")"
                return "((" + merged_args[0] + ") as f64)"
            if fn_name_raw == "bool" and len(merged_args) == 1:
                arg_t = self.normalize_type_name(self.get_expr_type(arg_nodes[0] if len(arg_nodes) > 0 else None))
                arg_any = self._is_any_type(arg_t)
                if not arg_any and len(arg_nodes) > 0 and (arg_t == "" or arg_t == "unknown"):
                    arg_any = self._is_any_type(self._dict_get_owner_value_type(arg_nodes[0]))
                if arg_any:
                    self.uses_pyany = True
                    return "py_any_to_bool(&" + merged_args[0] + ")"
                return "((" + merged_args[0] + ") != 0)"
            imported_sym = self._resolve_imported_symbol(fn_name_raw)
            imported_mod = self.any_dict_get_str(imported_sym, "module", "")
            if (
                fn_name_raw in {"save_gif", "write_rgb_png"}
                and imported_mod in {"pytra.runtime.gif", "pytra.utils.gif", "pytra.runtime.png", "pytra.utils.png"}
                and len(merged_args) > 0
            ):
                call_args = list(merged_args)
                call_args[0] = "&(" + call_args[0] + ")"
                if fn_name_raw == "write_rgb_png" and len(call_args) >= 4:
                    call_args[3] = "&(" + call_args[3] + ")"
                if fn_name_raw == "save_gif":
                    if len(call_args) >= 4:
                        call_args[3] = "&(" + call_args[3] + ")"
                    if len(call_args) >= 5:
                        call_args[4] = "&(" + call_args[4] + ")"
                return fn_name + "(" + ", ".join(call_args) + ")"
            ref_modes = self.function_arg_ref_modes.get(fn_name, [])
            call_args: list[str] = []
            i = 0
            while i < len(merged_args):
                arg_txt = merged_args[i]
                by_ref = i < len(ref_modes) and ref_modes[i]
                if by_ref:
                    arg_node = arg_nodes[i] if i < len(arg_nodes) else None
                    call_args.append(self._render_by_ref_call_arg(arg_txt, arg_node))
                else:
                    if i < len(arg_nodes):
                        t = self._infer_expr_type_for_call_arg(arg_nodes[i])
                        if self._should_clone_call_arg_type(t):
                            arg_txt = "(" + arg_txt + ").clone()"
                    call_args.append(arg_txt)
                i += 1
            return fn_name + "(" + ", ".join(call_args) + ")"

        if fn_kind == "Attribute":
            owner_expr = self.render_expr(fn_node.get("value"))
            owner_node = self.any_to_dict_or_empty(fn_node.get("value"))
            owner_type = self.get_expr_type(owner_node)
            owner_ctx = self.resolve_attribute_owner_context(fn_node.get("value"), owner_expr)
            owner_mod = self.any_dict_get_str(owner_ctx, "module", "")
            attr_raw = self.any_dict_get_str(fn_node, "attr", "")
            attr = self._safe_name(attr_raw)
            if owner_mod != "":
                if (
                    attr_raw in {"save_gif", "write_rgb_png"}
                    and owner_mod in {"pytra.runtime.gif", "pytra.utils.gif", "pytra.runtime.png", "pytra.utils.png"}
                    and len(merged_args) > 0
                ):
                    call_args = list(merged_args)
                    call_args[0] = "&(" + call_args[0] + ")"
                    if attr_raw == "write_rgb_png" and len(call_args) >= 4:
                        call_args[3] = "&(" + call_args[3] + ")"
                    if attr_raw == "save_gif":
                        if len(call_args) >= 4:
                            call_args[3] = "&(" + call_args[3] + ")"
                        if len(call_args) >= 5:
                            call_args[4] = "&(" + call_args[4] + ")"
                    return owner_mod.replace(".", "::") + "::" + attr_raw + "(" + ", ".join(call_args) + ")"
                call_args = self._clone_owned_call_args(merged_args, arg_nodes)
                return owner_mod.replace(".", "::") + "::" + attr_raw + "(" + ", ".join(call_args) + ")"
            if attr_raw == "items" and len(merged_args) == 0:
                return "(" + owner_expr + ").clone().into_iter()"
            if attr_raw == "keys" and len(merged_args) == 0:
                return "(" + owner_expr + ").keys().cloned()"
            if attr_raw == "values" and len(merged_args) == 0:
                return "(" + owner_expr + ").values().cloned()"
            if owner_type == "str" and attr_raw == "isdigit" and len(merged_args) == 0:
                self.uses_string_helpers = True
                return "py_isdigit(&" + owner_expr + ")"
            if owner_type == "str" and attr_raw == "isalpha" and len(merged_args) == 0:
                self.uses_string_helpers = True
                return "py_isalpha(&" + owner_expr + ")"
            if owner_type.startswith("list[") or owner_type in {"bytes", "bytearray"}:
                if attr_raw == "append" and len(merged_args) == 1:
                    if owner_type in {"bytes", "bytearray"}:
                        return owner_expr + ".push(((" + merged_args[0] + ") as u8))"
                    return owner_expr + ".push(" + merged_args[0] + ")"
                if attr_raw == "pop" and len(merged_args) == 0:
                    return owner_expr + ".pop().unwrap_or_default()"
                if attr_raw == "clear" and len(merged_args) == 0:
                    return owner_expr + ".clear()"
            if owner_type.startswith("dict["):
                key_t, owner_val_t = self._dict_key_value_types(owner_type)
                if attr_raw == "get" and len(merged_args) == 1:
                    key_expr = self._coerce_dict_key_expr(merged_args[0], key_t, require_owned=False)
                    return owner_expr + ".get(&" + key_expr + ").cloned().unwrap_or_default()"
                if attr_raw == "get" and len(merged_args) >= 2:
                    default_txt = merged_args[1]
                    if self._is_any_type(owner_val_t) and len(arg_nodes) >= 2:
                        self.uses_pyany = True
                        default_txt = self._render_as_pyany(arg_nodes[1])
                    key_expr = self._coerce_dict_key_expr(merged_args[0], key_t, require_owned=False)
                    return owner_expr + ".get(&" + key_expr + ").cloned().unwrap_or(" + default_txt + ")"
            owner_type_norm = self.normalize_type_name(owner_type)
            method_ref_modes = self.class_method_arg_ref_modes.get(owner_type_norm, {}).get(attr, [])
            if len(method_ref_modes) > 0:
                call_args: list[str] = []
                i = 0
                while i < len(merged_args):
                    arg_txt = merged_args[i]
                    by_ref = i < len(method_ref_modes) and method_ref_modes[i]
                    if by_ref:
                        arg_node = arg_nodes[i] if i < len(arg_nodes) else None
                        call_args.append(self._render_by_ref_call_arg(arg_txt, arg_node))
                    else:
                        call_args.append(arg_txt)
                    i += 1
                return owner_expr + "." + attr + "(" + ", ".join(call_args) + ")"
            return owner_expr + "." + attr + "(" + ", ".join(merged_args) + ")"

        fn_expr = self.render_expr(fn_node)
        call_args = self._clone_owned_call_args(merged_args, arg_nodes)
        return fn_expr + "(" + ", ".join(call_args) + ")"

    def render_expr(self, expr: Any) -> str:
        """式ノードを Rust へ描画する。"""
        expr_d = self.any_to_dict_or_empty(expr)
        if len(expr_d) == 0:
            return "()"
        kind = self.any_dict_get_str(expr_d, "kind", "")

        hook_specific = self.hook_on_render_expr_kind_specific(kind, expr_d)
        if hook_specific != "":
            return hook_specific
        hook_leaf = self.hook_on_render_expr_leaf(kind, expr_d)
        if hook_leaf != "":
            return hook_leaf

        if kind == "Name":
            name = self.any_dict_get_str(expr_d, "id", "_")
            return self._safe_name(name)
        if kind == "Constant":
            tag, non_str = self.render_constant_non_string_common(expr, expr_d, "()", "()")
            if tag == "1":
                return non_str
            val = self.any_to_str(expr_d.get("value"))
            return "(" + self.quote_string_literal(val) + ").to_string()"
        if kind == "Attribute":
            owner_node = self.any_to_dict_or_empty(expr_d.get("value"))
            owner = self.render_expr(owner_node)
            owner_ctx = self.resolve_attribute_owner_context(owner_node, owner)
            owner_mod = self.any_dict_get_str(owner_ctx, "module", "")
            attr_raw = self.any_dict_get_str(expr_d, "attr", "")
            if owner_mod != "":
                return owner_mod.replace(".", "::") + "::" + attr_raw
            owner_kind = self.any_dict_get_str(owner_node, "kind", "")
            attr = self._safe_name(attr_raw)
            if owner_kind == "Subscript":
                owner_owner_t = self.normalize_type_name(self.get_expr_type(owner_node.get("value")))
                owner_expr = owner
                if owner_owner_t.startswith("list[") or owner_owner_t.startswith("tuple[") or owner_owner_t in {"bytes", "bytearray"}:
                    owner_expr = self._render_subscript_lvalue(owner_node)
                attr_t = self.normalize_type_name(self.get_expr_type(expr_d))
                if self._is_copy_type(attr_t):
                    return owner_expr + "." + attr
                return "(" + owner_expr + "." + attr + ").clone()"
            return owner + "." + attr
        if kind == "UnaryOp":
            op = self.any_dict_get_str(expr_d, "op", "")
            right_node = self.any_to_dict_or_empty(expr_d.get("operand"))
            right = self.render_expr(right_node)
            right_kind = self.any_dict_get_str(right_node, "kind", "")
            simple_right = right_kind in {"Name", "Constant", "Call", "Attribute", "Subscript"}
            if op == "USub":
                return "-" + right if simple_right else "-(" + right + ")"
            if op == "Not":
                return "!" + right if simple_right else "!(" + right + ")"
            return right
        if kind == "BinOp":
            return self._render_binop(expr_d)
        if kind == "RangeExpr":
            return self._render_range_expr(expr_d)
        if kind == "Compare":
            return self._render_compare(expr_d)
        if kind == "BoolOp":
            vals = self.any_to_list(expr_d.get("values"))
            op = self.any_to_str(expr_d.get("op"))
            return self.render_boolop_common(vals, op, and_token="&&", or_token="||", empty_literal="false")
        if kind == "Call":
            call_hook = self.hook_on_render_call(expr_d, self.any_to_dict_or_empty(expr_d.get("func")), [], {})
            if call_hook != "":
                return call_hook
            return self._render_call(expr_d)
        if kind == "IfExp":
            return self._render_ifexp_expr(expr_d)
        if kind == "List":
            elts = self.any_to_list(expr_d.get("elts"))
            if len(elts) == 0:
                elts = self.any_to_list(expr_d.get("elements"))
            rendered: list[str] = []
            for elt in elts:
                rendered.append(self.render_expr(elt))
            return "vec![" + ", ".join(rendered) + "]"
        if kind == "Tuple":
            elts: list[Any] = self.tuple_elements(expr_d)
            rendered = []
            for elt in elts:
                rendered.append(self.render_expr(elt))
            if len(rendered) == 1:
                return "(" + rendered[0] + ",)"
            return "(" + ", ".join(rendered) + ")"
        if kind == "Dict":
            return self._render_dict_expr(expr_d, force_any_values=False)
        if kind == "ListComp":
            return self._render_list_comp(expr_d)
        if kind == "Subscript":
            owner_node = self.any_to_dict_or_empty(expr_d.get("value"))
            owner = self.render_expr(owner_node)
            owner_node_kind = self.any_dict_get_str(owner_node, "kind", "")
            if owner_node_kind == "Subscript":
                owner_owner_t = self.normalize_type_name(self.get_expr_type(owner_node.get("value")))
                if owner_owner_t.startswith("list[") or owner_owner_t.startswith("tuple[") or owner_owner_t in {"bytes", "bytearray"}:
                    owner = self._render_subscript_lvalue(owner_node)
            owner_t = self.normalize_type_name(self.get_expr_type(owner_node))
            slice_node = self.any_to_dict_or_empty(expr_d.get("slice"))
            slice_kind = self.any_dict_get_str(slice_node, "kind", "")
            if owner_t.startswith("dict["):
                key_t, _val_t = self._dict_key_value_types(owner_t)
                key_expr = self.render_expr(expr_d.get("slice"))
                key_expr = self._coerce_dict_key_expr(key_expr, key_t, require_owned=False)
                return owner + ".get(&" + key_expr + ").cloned().expect(\"dict key not found\")"
            if slice_kind == "Slice":
                self.uses_string_helpers = True
                start_node = slice_node.get("lower")
                end_node = slice_node.get("upper")
                start_txt = "None"
                end_txt = "None"
                if start_node is not None:
                    start_txt = "Some((" + self.render_expr(start_node) + ") as i64)"
                if end_node is not None:
                    end_txt = "Some((" + self.render_expr(end_node) + ") as i64)"
                if owner_t == "str":
                    return "py_slice_str(&" + owner + ", " + start_txt + ", " + end_txt + ")"
                return owner + "[" + self.render_expr(slice_node) + "]"
            idx = self.render_expr(expr_d.get("slice"))
            if owner_t == "str":
                self.uses_string_helpers = True
                return "py_str_at(&" + owner + ", ((" + idx + ") as i64))"
            idx_i64 = "((" + idx + ") as i64)"
            idx_usize = "((if " + idx_i64 + " < 0 { (" + owner + ".len() as i64 + " + idx_i64 + ") } else { " + idx_i64 + " }) as usize)"
            indexed = owner + "[" + idx_usize + "]"
            if owner_t in {"bytes", "bytearray"}:
                return "((" + indexed + ") as i64)"
            if owner_t.startswith("list["):
                elem_t = self._list_elem_type(owner_t)
                if self._is_copy_type(elem_t):
                    return indexed
                return "(" + indexed + ").clone()"
            return indexed
        if kind == "Slice":
            lower_node = expr_d.get("lower")
            upper_node = expr_d.get("upper")
            lower_txt = self.render_expr(lower_node) if lower_node is not None else ""
            upper_txt = self.render_expr(upper_node) if upper_node is not None else ""
            if lower_txt == "" and upper_txt == "":
                return ".."
            if lower_txt == "":
                return ".." + upper_txt
            if upper_txt == "":
                return lower_txt + ".."
            return lower_txt + ".." + upper_txt
        if kind == "Lambda":
            args = self.any_to_list(self.any_to_dict_or_empty(expr_d.get("args")).get("args"))
            names: list[str] = []
            for arg in args:
                names.append(self._safe_name(self.any_to_str(self.any_to_dict_or_empty(arg).get("arg"))))
            body = self.render_expr(expr_d.get("body"))
            return "|" + ", ".join(names) + "| " + body

        hook_complex = self.hook_on_render_expr_complex(expr_d)
        if hook_complex != "":
            return hook_complex
        return self.any_to_str(expr_d.get("repr"))

    def render_cond(self, expr: Any) -> str:
        """条件式向け描画（数値等を bool 条件へ寄せる）。"""
        return self.render_truthy_cond_common(
            expr,
            str_non_empty_pattern="!{expr}.is_empty()",
            collection_non_empty_pattern="{expr}.len() != 0",
            number_non_zero_pattern="{expr} != 0",
        )
def transpile_to_rust(east_doc: dict[str, Any]) -> str:
    """EAST ドキュメントを Rust コードへ変換する。"""
    emitter = RustEmitter(east_doc)
    return emitter.transpile()
