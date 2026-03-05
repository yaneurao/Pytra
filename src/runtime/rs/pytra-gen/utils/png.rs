// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

fn _png_append_list(mut dst: Vec<i64>, src: &[i64]) {
    let mut i = 0;
    let n = src.len() as i64;
    while i < n {
        dst.push(src[((i) as usize)]);
        i += 1;
    }
}

fn _crc32(data: &[i64]) -> i64 {
    let mut crc = 0xFFFFFFFF;
    let poly = 0xEDB88320;
    for b in (data).iter().copied() {
        crc = crc ^ b;
        let mut i = 0;
        while i < 8 {
            let lowbit = crc & 1;
            if lowbit != 0 {
                crc = crc >> 1 ^ poly;
            } else {
                crc = crc >> 1;
            }
            i += 1;
        }
    }
    return crc ^ 0xFFFFFFFF;
}

fn _adler32(data: &[i64]) -> i64 {
    let py_mod = 65521;
    let mut s1 = 1;
    let mut s2 = 0;
    for b in (data).iter().copied() {
        s1 += b;
        if s1 >= py_mod {
            s1 -= py_mod;
        }
        s2 += s1;
        s2 = s2 % py_mod;
    }
    return (s2 << 16 | s1) & 0xFFFFFFFF;
}

fn _png_u16le(v: i64) -> Vec<i64> {
    return vec![v & 0xFF, v >> 8 & 0xFF];
}

fn _png_u32be(v: i64) -> Vec<i64> {
    return vec![v >> 24 & 0xFF, v >> 16 & 0xFF, v >> 8 & 0xFF, v & 0xFF];
}

fn _zlib_deflate_store(data: &[i64]) -> Vec<i64> {
    let mut out: Vec<i64> = vec![];
    _png_append_list((out).clone(), &(vec![0x78, 0x01]));
    let n = data.len() as i64;
    let mut pos = 0;
    while pos < n {
        let remain = n - pos;
        let chunk_len = (if remain > 65535 { 65535 } else { remain });
        let final = (if pos + chunk_len >= n { 1 } else { 0 });
        out.push(final);
        _png_append_list((out).clone(), &(_png_u16le(chunk_len)));
        _png_append_list((out).clone(), &(_png_u16le(0xFFFF ^ chunk_len)));
        let mut i = pos;
        let end = pos + chunk_len;
        while i < end {
            out.push(data[((i) as usize)]);
            i += 1;
        }
        pos += chunk_len;
    }
    _png_append_list((out).clone(), &(_png_u32be(_adler32(data))));
    return out;
}

fn _chunk(chunk_type: &[i64], data: &[i64]) -> Vec<i64> {
    let crc_input: Vec<i64> = vec![];
    _png_append_list((crc_input).clone(), chunk_type);
    _png_append_list((crc_input).clone(), data);
    let crc = _crc32(&(crc_input)) & 0xFFFFFFFF;
    let out: Vec<i64> = vec![];
    _png_append_list((out).clone(), &(_png_u32be(data.len() as i64)));
    _png_append_list((out).clone(), chunk_type);
    _png_append_list((out).clone(), data);
    _png_append_list((out).clone(), &(_png_u32be(crc)));
    return out;
}

fn write_rgb_png(path: &str, width: i64, height: i64, pixels: &Vec<u8>) {
    let mut raw: Vec<i64> = vec![];
    for b in pixels {
        raw.push(((b) as i64));
    }
    let expected = width * height * 3;
    if raw.len() as i64 != expected {
        panic!("{}", format!("{}{}{}{}", ("pixels length mismatch: got=").to_string(), (raw.len() as i64).to_string(), (" expected=").to_string(), (expected).to_string()));
    }
    let mut scanlines: Vec<i64> = vec![];
    let row_bytes = width * 3;
    let mut y = 0;
    while y < height {
        scanlines.push(0);
        let start = y * row_bytes;
        let end = start + row_bytes;
        let mut i = start;
        while i < end {
            scanlines.push(raw[((if ((i) as i64) < 0 { (raw.len() as i64 + ((i) as i64)) } else { ((i) as i64) }) as usize)]);
            i += 1;
        }
        y += 1;
    }
    let ihdr: Vec<i64> = vec![];
    _png_append_list((ihdr).clone(), &(_png_u32be(width)));
    _png_append_list((ihdr).clone(), &(_png_u32be(height)));
    _png_append_list((ihdr).clone(), &(vec![8, 2, 0, 0, 0]));
    let idat = _zlib_deflate_store(&(scanlines));
    
    let png: Vec<i64> = vec![];
    _png_append_list((png).clone(), &(vec![137, 80, 78, 71, 13, 10, 26, 10]));
    _png_append_list((png).clone(), &(_chunk(&(vec![73, 72, 68, 82]), &(ihdr))));
    _png_append_list((png).clone(), &(_chunk(&(vec![73, 68, 65, 84]), &(idat))));
    let iend_data: Vec<i64> = vec![];
    _png_append_list((png).clone(), &(_chunk(&(vec![73, 69, 78, 68]), &(iend_data))));
    
    let f = open(path, ("wb").to_string());
    {
        f.write((png).clone());
    }
    {
        f.close();
    }
}

fn main() {
    ("PNG 書き出しユーティリティ（Python実行用）。\n\nこのモジュールは sample/py のスクリプトから利用し、\nRGB 8bit バッファを PNG ファイルとして保存する。\n").to_string();
}
