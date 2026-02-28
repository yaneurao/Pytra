use crate::time::perf_counter;
use crate::pytra::runtime::gif::save_gif;

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

// 16: Sample that ray-traces chaotic rotation of glass sculptures and outputs a GIF.

fn clamp01(v: f64) -> f64 {
    if v < 0.0 {
        return 0.0;
    }
    if v > 1.0 {
        return 1.0;
    }
    return v;
}

fn dot(ax: f64, ay: f64, az: f64, bx: f64, by: f64, bz: f64) -> f64 {
    return ax * bx + ay * by + az * bz;
}

fn length(x: f64, y: f64, z: f64) -> f64 {
    return math::sqrt(x * x + y * y + z * z);
}

fn normalize(x: f64, y: f64, z: f64) -> (f64, f64, f64) {
    let l = length(x, y, z);
    if l < 1e-9 {
        return (0.0, 0.0, 0.0);
    }
    return (x / l, y / l, z / l);
}

fn reflect(ix: f64, iy: f64, iz: f64, nx: f64, ny: f64, nz: f64) -> (f64, f64, f64) {
    let d = dot(ix, iy, iz, nx, ny, nz) * 2.0;
    return (ix - d * nx, iy - d * ny, iz - d * nz);
}

fn refract(ix: f64, iy: f64, iz: f64, nx: f64, ny: f64, nz: f64, eta: f64) -> (f64, f64, f64) {
    // Simple IOR-based refraction. Return reflection direction on total internal reflection.
    let cosi = -dot(ix, iy, iz, nx, ny, nz);
    let sint2 = eta * eta * (1.0 - cosi * cosi);
    if sint2 > 1.0 {
        return reflect(ix, iy, iz, nx, ny, nz);
    }
    let cost = math::sqrt(1.0 - sint2);
    let k = eta * cosi - cost;
    return (eta * ix + k * nx, eta * iy + k * ny, eta * iz + k * nz);
}

fn schlick(cos_theta: f64, f0: f64) -> f64 {
    let m = 1.0 - cos_theta;
    return f0 + (1.0 - f0) * m * m * m * m * m;
}

fn sky_color(dx: f64, dy: f64, dz: f64, tphase: f64) -> (f64, f64, f64) {
    // Sky gradient + neon band
    let t = 0.5 * (dy + 1.0);
    let mut r = 0.06 + 0.20 * t;
    let mut g = 0.10 + 0.25 * t;
    let mut b = 0.16 + 0.45 * t;
    let band = 0.5 + 0.5 * math::sin(8.0 * dx + 6.0 * dz + tphase);
    r += py_any_to_f64(&(0.08 * band));
    g += py_any_to_f64(&(0.05 * band));
    b += py_any_to_f64(&(0.12 * band));
    return (clamp01(r), clamp01(g), clamp01(b));
}

fn sphere_intersect(ox: f64, oy: f64, oz: f64, dx: f64, dy: f64, dz: f64, cx: f64, cy: f64, cz: f64, radius: f64) -> f64 {
    let lx = ox - cx;
    let ly = oy - cy;
    let lz = oz - cz;
    let b = lx * dx + ly * dy + lz * dz;
    let c = lx * lx + ly * ly + lz * lz - radius * radius;
    let h = b * b - c;
    if h < 0.0 {
        return -1.0;
    }
    let s = math::sqrt(h);
    let t0 = -b - s;
    if t0 > 1e-4 {
        return t0;
    }
    let t1 = -b + s;
    if t1 > 1e-4 {
        return t1;
    }
    return -1.0;
}

fn palette_332() -> Vec<u8> {
    // 3-3-2 quantized palette. Lightweight quantization that stays fast after transpilation.
    let mut p = vec![0u8; (256 * 3) as usize];
    let __hoisted_cast_1: f64 = ((7) as f64);
    let __hoisted_cast_2: f64 = ((3) as f64);
    let mut i: i64 = 0;
    while i < 256 {
        let r = i >> 5 & 7;
        let g = i >> 2 & 7;
        let b = i & 3;
        let __idx_i64_1 = ((i * 3 + 0) as i64);
        let __idx_2 = if __idx_i64_1 < 0 { (p.len() as i64 + __idx_i64_1) as usize } else { __idx_i64_1 as usize };
        p[__idx_2] = ((((((255 * r) as f64) / __hoisted_cast_1) as i64)) as u8);
        let __idx_i64_3 = ((i * 3 + 1) as i64);
        let __idx_4 = if __idx_i64_3 < 0 { (p.len() as i64 + __idx_i64_3) as usize } else { __idx_i64_3 as usize };
        p[__idx_4] = ((((((255 * g) as f64) / __hoisted_cast_1) as i64)) as u8);
        let __idx_i64_5 = ((i * 3 + 2) as i64);
        let __idx_6 = if __idx_i64_5 < 0 { (p.len() as i64 + __idx_i64_5) as usize } else { __idx_i64_5 as usize };
        p[__idx_6] = ((((((255 * b) as f64) / __hoisted_cast_2) as i64)) as u8);
        i += 1;
    }
    return (p).clone();
}

fn quantize_332(r: f64, g: f64, b: f64) -> i64 {
    let rr = ((clamp01(r) * 255.0) as i64);
    let gg = ((clamp01(g) * 255.0) as i64);
    let bb = ((clamp01(b) * 255.0) as i64);
    return (rr >> 5 << 5) + (gg >> 5 << 2) + (bb >> 6);
}

fn render_frame(width: i64, height: i64, frame_id: i64, frames_n: i64) -> Vec<u8> {
    let t = ((frame_id) as f64) / ((frames_n) as f64);
    let tphase = 2.0 * math::pi * t;
    
    // Camera slowly orbits.
    let cam_r = 3.0;
    let cam_x = cam_r * math::cos(tphase * 0.9);
    let cam_y = 1.1 + 0.25 * math::sin(tphase * 0.6);
    let cam_z = cam_r * math::sin(tphase * 0.9);
    let look_x = 0.0;
    let look_y = 0.35;
    let look_z = 0.0;
    
    let __tmp_7 = normalize(look_x - cam_x, look_y - cam_y, look_z - cam_z);
    let fwd_x = __tmp_7.0;
    let fwd_y = __tmp_7.1;
    let fwd_z = __tmp_7.2;
    let __tmp_8 = normalize(fwd_z, 0.0, -fwd_x);
    let right_x = __tmp_8.0;
    let right_y = __tmp_8.1;
    let right_z = __tmp_8.2;
    let __tmp_9 = normalize(right_y * fwd_z - right_z * fwd_y, right_z * fwd_x - right_x * fwd_z, right_x * fwd_y - right_y * fwd_x);
    let up_x = __tmp_9.0;
    let up_y = __tmp_9.1;
    let up_z = __tmp_9.2;
    
    // Moving glass sculpture (3 spheres) and an emissive sphere.
    let s0x = 0.9 * math::cos(1.3 * tphase);
    let s0y = 0.15 + 0.35 * math::sin(1.7 * tphase);
    let s0z = 0.9 * math::sin(1.3 * tphase);
    let s1x = 1.2 * math::cos(1.3 * tphase + 2.094);
    let s1y = 0.10 + 0.40 * math::sin(1.1 * tphase + 0.8);
    let s1z = 1.2 * math::sin(1.3 * tphase + 2.094);
    let s2x = 1.0 * math::cos(1.3 * tphase + 4.188);
    let s2y = 0.20 + 0.30 * math::sin(1.5 * tphase + 1.9);
    let s2z = 1.0 * math::sin(1.3 * tphase + 4.188);
    let lr = 0.35;
    let lx = 2.4 * math::cos(tphase * 1.8);
    let ly = 1.8 + 0.8 * math::sin(tphase * 1.2);
    let lz = 2.4 * math::sin(tphase * 1.8);
    
    let mut frame = vec![0u8; (width * height) as usize];
    let aspect = ((width) as f64) / ((height) as f64);
    let fov = 1.25;
    let __hoisted_cast_3: f64 = ((height) as f64);
    let __hoisted_cast_4: f64 = ((width) as f64);
    
    let mut py: i64 = 0;
    while py < height {
        let row_base = py * width;
        let sy = 1.0 - 2.0 * (((py) as f64) + 0.5) / __hoisted_cast_3;
        let mut px: i64 = 0;
        while px < width {
            let sx = (2.0 * (((px) as f64) + 0.5) / __hoisted_cast_4 - 1.0) * aspect;
            let rx = fwd_x + fov * (sx * right_x + sy * up_x);
            let ry = fwd_y + fov * (sx * right_y + sy * up_y);
            let rz = fwd_z + fov * (sx * right_z + sy * up_z);
            let __tmp_10 = normalize(rx, ry, rz);
            let dx = __tmp_10.0;
            let dy = __tmp_10.1;
            let dz = __tmp_10.2;
            
            // Search for the nearest hit.
            let mut best_t = 1e9;
            let mut hit_kind = 0;
            let mut r = 0.0;
            let mut g = 0.0;
            let mut b = 0.0;
            
            // Floor plane y=-1.2
            if dy < -1e-6 {
                let tf = (-1.2 - cam_y) / dy;
                if (tf > 1e-4) && (tf < best_t) {
                    best_t = py_any_to_f64(&(tf));
                    hit_kind = 1;
                }
            }
            let t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
            if (t0 > 0.0) && (t0 < best_t) {
                best_t = t0;
                hit_kind = 2;
            }
            let t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
            if (t1 > 0.0) && (t1 < best_t) {
                best_t = t1;
                hit_kind = 3;
            }
            let t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
            if (t2 > 0.0) && (t2 < best_t) {
                best_t = t2;
                hit_kind = 4;
            }
            if hit_kind == 0 {
                let __tmp_11 = sky_color(dx, dy, dz, tphase);
                r = __tmp_11.0;
                g = __tmp_11.1;
                b = __tmp_11.2;
            } else {
                if hit_kind == 1 {
                    let mut hx = cam_x + best_t * dx;
                    let mut hz = cam_z + best_t * dz;
                    let mut cx = ((math::floor(hx * 2.0)) as i64);
                    let mut cz = ((math::floor(hz * 2.0)) as i64);
                    let checker = (if (cx + cz) % 2 == 0 { 0 } else { 1 });
                    let base_r = (if checker == 0 { 0.10 } else { 0.04 });
                    let base_g = (if checker == 0 { 0.11 } else { 0.05 });
                    let base_b = (if checker == 0 { 0.13 } else { 0.08 });
                    // Emissive sphere contribution.
                    let mut lxv = lx - hx;
                    let mut lyv = ly - -1.2;
                    let mut lzv = lz - hz;
                    let __tmp_12 = normalize(lxv, lyv, lzv);
                    let mut ldx = __tmp_12.0;
                    let mut ldy = __tmp_12.1;
                    let mut ldz = __tmp_12.2;
                    let mut ndotl = (if ldy > 0.0 { ldy } else { 0.0 });
                    let ldist2 = lxv * lxv + lyv * lyv + lzv * lzv;
                    let mut glow = 8.0 / (1.0 + ldist2);
                    r = py_any_to_f64(&(base_r + 0.8 * glow + 0.20 * ndotl));
                    g = py_any_to_f64(&(base_g + 0.5 * glow + 0.18 * ndotl));
                    b = py_any_to_f64(&(base_b + 1.0 * glow + 0.24 * ndotl));
                } else {
                    let mut cx = 0.0;
                    let mut cy = 0.0;
                    let mut cz = 0.0;
                    let mut rad = 1.0;
                    if hit_kind == 2 {
                        cx = py_any_to_f64(&(s0x));
                        cy = py_any_to_f64(&(s0y));
                        cz = py_any_to_f64(&(s0z));
                        rad = 0.65;
                    } else {
                        if hit_kind == 3 {
                            cx = py_any_to_f64(&(s1x));
                            cy = py_any_to_f64(&(s1y));
                            cz = py_any_to_f64(&(s1z));
                            rad = 0.72;
                        } else {
                            cx = py_any_to_f64(&(s2x));
                            cy = py_any_to_f64(&(s2y));
                            cz = py_any_to_f64(&(s2z));
                            rad = 0.58;
                        }
                    }
                    let mut hx = cam_x + best_t * dx;
                    let hy = cam_y + best_t * dy;
                    let mut hz = cam_z + best_t * dz;
                    let __tmp_13 = normalize((hx - cx) / rad, (hy - cy) / rad, (hz - cz) / rad);
                    let nx = __tmp_13.0;
                    let ny = __tmp_13.1;
                    let nz = __tmp_13.2;
                    
                    // Simple glass shading (reflection + refraction + light highlights).
                    let __tmp_14 = reflect(dx, dy, dz, nx, ny, nz);
                    let rdx = __tmp_14.0;
                    let rdy = __tmp_14.1;
                    let rdz = __tmp_14.2;
                    let __tmp_15 = refract(dx, dy, dz, nx, ny, nz, 1.0 / 1.45);
                    let tdx = __tmp_15.0;
                    let tdy = __tmp_15.1;
                    let tdz = __tmp_15.2;
                    let __tmp_16 = sky_color(rdx, rdy, rdz, tphase);
                    let sr = __tmp_16.0;
                    let sg = __tmp_16.1;
                    let sb = __tmp_16.2;
                    let __tmp_17 = sky_color(tdx, tdy, tdz, tphase + 0.8);
                    let tr = __tmp_17.0;
                    let tg = __tmp_17.1;
                    let tb = __tmp_17.2;
                    let cosi = (if -(dx * nx + dy * ny + dz * nz) > 0.0 { -(dx * nx + dy * ny + dz * nz) } else { 0.0 });
                    let fr = schlick(cosi, 0.04);
                    r = py_any_to_f64(&(tr * (1.0 - fr) + sr * fr));
                    g = py_any_to_f64(&(tg * (1.0 - fr) + sg * fr));
                    b = py_any_to_f64(&(tb * (1.0 - fr) + sb * fr));
                    
                    let mut lxv = lx - hx;
                    let mut lyv = ly - hy;
                    let mut lzv = lz - hz;
                    let __tmp_18 = normalize(lxv, lyv, lzv);
                    let mut ldx = __tmp_18.0;
                    let mut ldy = __tmp_18.1;
                    let mut ldz = __tmp_18.2;
                    let mut ndotl = (if nx * ldx + ny * ldy + nz * ldz > 0.0 { nx * ldx + ny * ldy + nz * ldz } else { 0.0 });
                    let __tmp_19 = normalize(ldx - dx, ldy - dy, ldz - dz);
                    let hvx = __tmp_19.0;
                    let hvy = __tmp_19.1;
                    let hvz = __tmp_19.2;
                    let ndoth = (if nx * hvx + ny * hvy + nz * hvz > 0.0 { nx * hvx + ny * hvy + nz * hvz } else { 0.0 });
                    let mut spec = ndoth * ndoth;
                    spec = spec * spec;
                    spec = spec * spec;
                    spec = spec * spec;
                    let mut glow = 10.0 / (1.0 + lxv * lxv + lyv * lyv + lzv * lzv);
                    r += 0.20 * ndotl + 0.80 * spec + 0.45 * glow;
                    g += 0.18 * ndotl + 0.60 * spec + 0.35 * glow;
                    b += 0.26 * ndotl + 1.00 * spec + 0.65 * glow;
                    
                    // Slight tint variation per sphere.
                    if hit_kind == 2 {
                        r *= 0.95;
                        g *= 1.05;
                        b *= 1.10;
                    } else {
                        if hit_kind == 3 {
                            r *= 1.08;
                            g *= 0.98;
                            b *= 1.04;
                        } else {
                            r *= 1.02;
                            g *= 1.10;
                            b *= 0.95;
                        }
                    }
                }
            }
            // Slightly stronger tone mapping.
            r = py_any_to_f64(&(math::sqrt(clamp01(r))));
            g = py_any_to_f64(&(math::sqrt(clamp01(g))));
            b = py_any_to_f64(&(math::sqrt(clamp01(b))));
            let __idx_i64_20 = ((row_base + px) as i64);
            let __idx_21 = if __idx_i64_20 < 0 { (frame.len() as i64 + __idx_i64_20) as usize } else { __idx_i64_20 as usize };
            frame[__idx_21] = ((quantize_332(r, g, b)) as u8);
            px += 1;
        }
        py += 1;
    }
    return (frame).clone();
}

fn run_16_glass_sculpture_chaos() {
    let width = 320;
    let height = 240;
    let frames_n = 72;
    let out_path = ("sample/out/16_glass_sculpture_chaos.gif").to_string();
    
    let start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut i: i64 = 0;
    while i < frames_n {
        frames.push(render_frame(width, height, i, frames_n));
        i += 1;
    }
    save_gif(&(out_path), width, height, &(frames), &(palette_332()), 6, 0);
    let elapsed = perf_counter() - start;
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {}", ("frames:").to_string(), frames_n);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_16_glass_sculpture_chaos();
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
