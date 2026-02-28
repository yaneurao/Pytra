use crate::pytra::runtime::png;
use crate::time::perf_counter;

use std::fs;
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

    out.extend_from_slice(b"\x21\xFF\x0BNETSCAPE2.0\x03\x01");
    out.extend_from_slice(&(loop_count as u16).to_le_bytes());
    out.push(0);

    for fr in frames.iter() {
        out.extend_from_slice(b"\x21\xF9\x04\x00");
        out.extend_from_slice(&(delay_cs as u16).to_le_bytes());
        out.extend_from_slice(b"\x00\x00");

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

// 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
// Dependencies are kept minimal (time only) for transpilation compatibility.

fn clamp01(v: f64) -> f64 {
    if v < 0.0 {
        return 0.0;
    }
    if v > 1.0 {
        return 1.0;
    }
    return v;
}

fn hit_sphere(ox: f64, oy: f64, oz: f64, dx: f64, dy: f64, dz: f64, cx: f64, cy: f64, cz: f64, r: f64) -> f64 {
    let lx: f64 = ox - cx;
    let ly: f64 = oy - cy;
    let lz: f64 = oz - cz;
    
    let a: f64 = dx * dx + dy * dy + dz * dz;
    let b: f64 = 2.0 * (lx * dx + ly * dy + lz * dz);
    let c: f64 = lx * lx + ly * ly + lz * lz - r * r;
    
    let d: f64 = b * b - 4.0 * a * c;
    if d < 0.0 {
        return -1.0;
    }
    let sd: f64 = py_any_to_f64(&(math::sqrt(d)));
    let t0: f64 = (-b - sd) / (2.0 * a);
    let t1: f64 = (-b + sd) / (2.0 * a);
    
    if t0 > 0.001 {
        return t0;
    }
    if t1 > 0.001 {
        return t1;
    }
    return -1.0;
}

fn render(width: i64, height: i64, aa: i64) -> Vec<u8> {
    let mut pixels: Vec<u8> = Vec::<u8>::with_capacity(((((width) * (height)) * 3)) as usize);
    
    // Camera origin
    let ox: f64 = 0.0;
    let oy: f64 = 0.0;
    let oz: f64 = -3.0;
    
    // Light direction (normalized)
    let lx: f64 = -0.4;
    let ly: f64 = 0.8;
    let lz: f64 = -0.45;
    let __hoisted_cast_1: f64 = ((aa) as f64);
    let __hoisted_cast_2: f64 = ((height - 1) as f64);
    let __hoisted_cast_3: f64 = ((width - 1) as f64);
    let __hoisted_cast_4: f64 = ((height) as f64);
    
    let mut y: i64 = 0;
    while y < height {
        let mut x: i64 = 0;
        while x < width {
            let mut ar: i64 = 0;
            let mut ag: i64 = 0;
            let mut ab: i64 = 0;
            
            let mut ay: i64 = 0;
            while ay < aa {
                let mut ax: i64 = 0;
                while ax < aa {
                    let fy = (((y) as f64) + (((ay) as f64) + 0.5) / __hoisted_cast_1) / __hoisted_cast_2;
                    let fx = (((x) as f64) + (((ax) as f64) + 0.5) / __hoisted_cast_1) / __hoisted_cast_3;
                    let sy: f64 = 1.0 - 2.0 * fy;
                    let sx: f64 = (2.0 * fx - 1.0) * (((width) as f64) / __hoisted_cast_4);
                    
                    let mut dx: f64 = sx;
                    let mut dy: f64 = sy;
                    let mut dz: f64 = 1.0;
                    let inv_len: f64 = py_any_to_f64(&(1.0 / math::sqrt(dx * dx + dy * dy + dz * dz)));
                    dx *= inv_len;
                    dy *= inv_len;
                    dz *= inv_len;
                    
                    let mut t_min: f64 = 1.0e30;
                    let mut hit_id: i64 = -1;
                    
                    let mut t: f64 = hit_sphere(ox, oy, oz, dx, dy, dz, -0.8, -0.2, 2.2, 0.8);
                    if (t > 0.0) && (t < t_min) {
                        t_min = t;
                        hit_id = 0;
                    }
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95);
                    if (t > 0.0) && (t < t_min) {
                        t_min = t;
                        hit_id = 1;
                    }
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, -1001.0, 3.0, 1000.0);
                    if (t > 0.0) && (t < t_min) {
                        t_min = t;
                        hit_id = 2;
                    }
                    let mut r: i64 = 0;
                    let mut g: i64 = 0;
                    let mut b: i64 = 0;
                    
                    if hit_id >= 0 {
                        let px: f64 = ox + dx * t_min;
                        let py: f64 = oy + dy * t_min;
                        let pz: f64 = oz + dz * t_min;
                        
                        let mut nx: f64 = 0.0;
                        let mut ny: f64 = 0.0;
                        let mut nz: f64 = 0.0;
                        
                        if hit_id == 0 {
                            nx = (px + 0.8) / 0.8;
                            ny = (py + 0.2) / 0.8;
                            nz = (pz - 2.2) / 0.8;
                        } else {
                            if hit_id == 1 {
                                nx = (px - 0.9) / 0.95;
                                ny = (py - 0.1) / 0.95;
                                nz = (pz - 2.9) / 0.95;
                            } else {
                                nx = 0.0;
                                ny = 1.0;
                                nz = 0.0;
                            }
                        }
                        let mut diff: f64 = nx * -lx + ny * -ly + nz * -lz;
                        diff = clamp01(diff);
                        
                        let mut base_r: f64 = 0.0;
                        let mut base_g: f64 = 0.0;
                        let mut base_b: f64 = 0.0;
                        
                        if hit_id == 0 {
                            base_r = 0.95;
                            base_g = 0.35;
                            base_b = 0.25;
                        } else {
                            if hit_id == 1 {
                                base_r = 0.25;
                                base_g = 0.55;
                                base_b = 0.95;
                            } else {
                                let checker: i64 = (((px + 50.0) * 0.8) as i64) + (((pz + 50.0) * 0.8) as i64);
                                if checker % 2 == 0 {
                                    base_r = 0.85;
                                    base_g = 0.85;
                                    base_b = 0.85;
                                } else {
                                    base_r = 0.2;
                                    base_g = 0.2;
                                    base_b = 0.2;
                                }
                            }
                        }
                        let shade: f64 = 0.12 + 0.88 * diff;
                        r = ((255.0 * clamp01(base_r * shade)) as i64);
                        g = ((255.0 * clamp01(base_g * shade)) as i64);
                        b = ((255.0 * clamp01(base_b * shade)) as i64);
                    } else {
                        let tsky: f64 = 0.5 * (dy + 1.0);
                        r = ((255.0 * (0.65 + 0.20 * tsky)) as i64);
                        g = ((255.0 * (0.75 + 0.18 * tsky)) as i64);
                        b = ((255.0 * (0.90 + 0.08 * tsky)) as i64);
                    }
                    ar += r;
                    ag += g;
                    ab += b;
                    ax += 1;
                }
                ay += 1;
            }
            let samples = aa * aa;
            pixels.push(((ar / samples) as u8));
            pixels.push(((ag / samples) as u8));
            pixels.push(((ab / samples) as u8));
            x += 1;
        }
        y += 1;
    }
    return pixels;
}

fn run_raytrace() {
    let width: i64 = 1600;
    let height: i64 = 900;
    let aa: i64 = 2;
    let out_path: String = ("sample/out/02_raytrace_spheres.png").to_string();
    
    let start: f64 = perf_counter();
    let pixels: Vec<u8> = render(width, height, aa);
    pytra::runtime::png::write_rgb_png(&(out_path), width, height, &(pixels));
    let elapsed: f64 = perf_counter() - start;
    
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {} {} {}", ("size:").to_string(), width, ("x").to_string(), height);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_raytrace();
}

#[derive(Clone, Debug, Default)]
enum PyAny {
    Int(i64),
    Float(f64),
    Bool(bool),
    Str(String),
    Dict(::std::collections::BTreeMap<String, PyAny>),
    List(Vec<PyAny>),
    Set(Vec<PyAny>),
    #[default]
    None,
}

fn py_any_as_dict(v: PyAny) -> ::std::collections::BTreeMap<String, PyAny> {
    match v {
        PyAny::Dict(d) => d,
        _ => ::std::collections::BTreeMap::new(),
    }
}

trait PyAnyToI64Arg {
    fn py_any_to_i64_arg(&self) -> i64;
}
impl PyAnyToI64Arg for PyAny {
    fn py_any_to_i64_arg(&self) -> i64 {
        match self {
            PyAny::Int(n) => *n,
            PyAny::Float(f) => *f as i64,
            PyAny::Bool(b) => if *b { 1 } else { 0 },
            PyAny::Str(s) => s.parse::<i64>().unwrap_or(0),
            _ => 0,
        }
    }
}
impl PyAnyToI64Arg for i64 {
    fn py_any_to_i64_arg(&self) -> i64 { *self }
}
impl PyAnyToI64Arg for i32 {
    fn py_any_to_i64_arg(&self) -> i64 { *self as i64 }
}
impl PyAnyToI64Arg for f64 {
    fn py_any_to_i64_arg(&self) -> i64 { *self as i64 }
}
impl PyAnyToI64Arg for f32 {
    fn py_any_to_i64_arg(&self) -> i64 { *self as i64 }
}
impl PyAnyToI64Arg for bool {
    fn py_any_to_i64_arg(&self) -> i64 { if *self { 1 } else { 0 } }
}
impl PyAnyToI64Arg for String {
    fn py_any_to_i64_arg(&self) -> i64 { self.parse::<i64>().unwrap_or(0) }
}
impl PyAnyToI64Arg for str {
    fn py_any_to_i64_arg(&self) -> i64 { self.parse::<i64>().unwrap_or(0) }
}
fn py_any_to_i64<T: PyAnyToI64Arg + ?Sized>(v: &T) -> i64 {
    v.py_any_to_i64_arg()
}

trait PyAnyToF64Arg {
    fn py_any_to_f64_arg(&self) -> f64;
}
impl PyAnyToF64Arg for PyAny {
    fn py_any_to_f64_arg(&self) -> f64 {
        match self {
            PyAny::Int(n) => *n as f64,
            PyAny::Float(f) => *f,
            PyAny::Bool(b) => if *b { 1.0 } else { 0.0 },
            PyAny::Str(s) => s.parse::<f64>().unwrap_or(0.0),
            _ => 0.0,
        }
    }
}
impl PyAnyToF64Arg for f64 {
    fn py_any_to_f64_arg(&self) -> f64 { *self }
}
impl PyAnyToF64Arg for f32 {
    fn py_any_to_f64_arg(&self) -> f64 { *self as f64 }
}
impl PyAnyToF64Arg for i64 {
    fn py_any_to_f64_arg(&self) -> f64 { *self as f64 }
}
impl PyAnyToF64Arg for i32 {
    fn py_any_to_f64_arg(&self) -> f64 { *self as f64 }
}
impl PyAnyToF64Arg for bool {
    fn py_any_to_f64_arg(&self) -> f64 { if *self { 1.0 } else { 0.0 } }
}
impl PyAnyToF64Arg for String {
    fn py_any_to_f64_arg(&self) -> f64 { self.parse::<f64>().unwrap_or(0.0) }
}
impl PyAnyToF64Arg for str {
    fn py_any_to_f64_arg(&self) -> f64 { self.parse::<f64>().unwrap_or(0.0) }
}
fn py_any_to_f64<T: PyAnyToF64Arg + ?Sized>(v: &T) -> f64 {
    v.py_any_to_f64_arg()
}

trait PyAnyToBoolArg {
    fn py_any_to_bool_arg(&self) -> bool;
}
impl PyAnyToBoolArg for PyAny {
    fn py_any_to_bool_arg(&self) -> bool {
        match self {
            PyAny::Int(n) => *n != 0,
            PyAny::Float(f) => *f != 0.0,
            PyAny::Bool(b) => *b,
            PyAny::Str(s) => !s.is_empty(),
            PyAny::Dict(d) => !d.is_empty(),
            PyAny::List(xs) => !xs.is_empty(),
            PyAny::Set(xs) => !xs.is_empty(),
            PyAny::None => false,
        }
    }
}
impl PyAnyToBoolArg for bool {
    fn py_any_to_bool_arg(&self) -> bool { *self }
}
impl PyAnyToBoolArg for i64 {
    fn py_any_to_bool_arg(&self) -> bool { *self != 0 }
}
impl PyAnyToBoolArg for f64 {
    fn py_any_to_bool_arg(&self) -> bool { *self != 0.0 }
}
impl PyAnyToBoolArg for String {
    fn py_any_to_bool_arg(&self) -> bool { !self.is_empty() }
}
impl PyAnyToBoolArg for str {
    fn py_any_to_bool_arg(&self) -> bool { !self.is_empty() }
}
fn py_any_to_bool<T: PyAnyToBoolArg + ?Sized>(v: &T) -> bool {
    v.py_any_to_bool_arg()
}

trait PyAnyToStringArg {
    fn py_any_to_string_arg(&self) -> String;
}
impl PyAnyToStringArg for PyAny {
    fn py_any_to_string_arg(&self) -> String {
        match self {
            PyAny::Int(n) => n.to_string(),
            PyAny::Float(f) => f.to_string(),
            PyAny::Bool(b) => b.to_string(),
            PyAny::Str(s) => s.clone(),
            PyAny::Dict(d) => format!("{:?}", d),
            PyAny::List(xs) => format!("{:?}", xs),
            PyAny::Set(xs) => format!("{:?}", xs),
            PyAny::None => String::new(),
        }
    }
}
impl PyAnyToStringArg for String {
    fn py_any_to_string_arg(&self) -> String { self.clone() }
}
impl PyAnyToStringArg for str {
    fn py_any_to_string_arg(&self) -> String { self.to_string() }
}
impl PyAnyToStringArg for i64 {
    fn py_any_to_string_arg(&self) -> String { self.to_string() }
}
impl PyAnyToStringArg for f64 {
    fn py_any_to_string_arg(&self) -> String { self.to_string() }
}
impl PyAnyToStringArg for bool {
    fn py_any_to_string_arg(&self) -> String { self.to_string() }
}
fn py_any_to_string<T: PyAnyToStringArg + ?Sized>(v: &T) -> String {
    v.py_any_to_string_arg()
}
