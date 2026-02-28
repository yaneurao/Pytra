use crate::time::perf_counter;
use crate::pytra::runtime::gif::grayscale_palette;
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

// 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

fn render_frame(width: i64, height: i64, center_x: f64, center_y: f64, scale: f64, max_iter: i64) -> Vec<u8> {
    let mut frame = vec![0u8; (width * height) as usize];
    let __hoisted_cast_1: f64 = ((max_iter) as f64);
    let mut y: i64 = 0;
    while y < height {
        let row_base = y * width;
        let cy = center_y + (((y) as f64) - ((height) as f64) * 0.5) * scale;
        let mut x: i64 = 0;
        while x < width {
            let cx = center_x + (((x) as f64) - ((width) as f64) * 0.5) * scale;
            let mut zx = 0.0;
            let mut zy = 0.0;
            let mut i = 0;
            while i < max_iter {
                let zx2 = zx * zx;
                let zy2 = zy * zy;
                if zx2 + zy2 > 4.0 {
                    break;
                }
                zy = 2.0 * zx * zy + cy;
                zx = zx2 - zy2 + cx;
                i += 1;
            }
            let __idx_i64_1 = ((row_base + x) as i64);
            let __idx_2 = if __idx_i64_1 < 0 { (frame.len() as i64 + __idx_i64_1) as usize } else { __idx_i64_1 as usize };
            frame[__idx_2] = ((((255.0 * ((i) as f64) / __hoisted_cast_1) as i64)) as u8);
            x += 1;
        }
        y += 1;
    }
    return (frame).clone();
}

fn run_05_mandelbrot_zoom() {
    let width = 320;
    let height = 240;
    let frame_count = 48;
    let max_iter = 110;
    let center_x = -0.743643887037151;
    let center_y = 0.13182590420533;
    let base_scale = 3.2 / ((width) as f64);
    let zoom_per_frame = 0.93;
    let out_path = ("sample/out/05_mandelbrot_zoom.gif").to_string();
    
    let start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut scale = base_scale;
    let mut py_underscore: i64 = 0;
    while py_underscore < frame_count {
        frames.push(render_frame(width, height, center_x, center_y, scale, max_iter));
        scale *= zoom_per_frame;
        py_underscore += 1;
    }
    save_gif(&(out_path), width, height, &(frames), &(grayscale_palette()), 5, 0);
    let elapsed = perf_counter() - start;
    println!("{} {}", ("output:").to_string(), out_path);
    println!("{} {}", ("frames:").to_string(), frame_count);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_05_mandelbrot_zoom();
}
