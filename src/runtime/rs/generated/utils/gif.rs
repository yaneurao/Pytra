// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::abi;

fn _gif_append_list(mut dst: Vec<i64>, src: &[i64]) {
    let mut i = 0;
    let n = src.len() as i64;
    while i < n {
        dst.push(src[((i) as usize)]);
        i += 1;
    }
}

fn _gif_u16le(v: i64) -> Vec<i64> {
    return vec![v & 0xFF, v >> 8 & 0xFF];
}

fn _lzw_encode(data: &Vec<u8>, min_code_size: i64) -> Vec<u8> {
    if data.len() as i64 == 0 {
        return (vec![]).clone();
    }
    let clear_code = 1 << min_code_size;
    let end_code = clear_code + 1;
    let mut code_size = min_code_size + 1;
    
    let mut out: Vec<i64> = vec![];
    let mut bit_buffer = 0;
    let mut bit_count = 0;
    
    bit_buffer |= clear_code << bit_count;
    bit_count += code_size;
    while bit_count >= 8 {
        out.push(bit_buffer & 0xFF);
        bit_buffer = bit_buffer >> 8;
        bit_count -= 8;
    }
    code_size = min_code_size + 1;
    
    for v in data {
        bit_buffer |= py_any_to_i64(&v << bit_count);
        bit_count += code_size;
        while bit_count >= 8 {
            out.push(bit_buffer & 0xFF);
            bit_buffer = bit_buffer >> 8;
            bit_count -= 8;
        }
        bit_buffer |= clear_code << bit_count;
        bit_count += code_size;
        while bit_count >= 8 {
            out.push(bit_buffer & 0xFF);
            bit_buffer = bit_buffer >> 8;
            bit_count -= 8;
        }
        code_size = min_code_size + 1;
    }
    bit_buffer |= end_code << bit_count;
    bit_count += code_size;
    while bit_count >= 8 {
        out.push(bit_buffer & 0xFF);
        bit_buffer = bit_buffer >> 8;
        bit_count -= 8;
    }
    if bit_count > 0 {
        out.push(bit_buffer & 0xFF);
    }
    return (out).clone();
}

fn grayscale_palette() -> Vec<u8> {
    let mut p: Vec<i64> = vec![];
    let mut i = 0;
    while i < 256 {
        p.push(i);
        p.push(i);
        p.push(i);
        i += 1;
    }
    return (p).clone();
}

fn save_gif(path: &str, width: i64, height: i64, frames: &[Vec<u8>], palette: &Vec<u8>, delay_cs: i64, py_loop: i64) {
    if palette.len() as i64 != 256 * 3 {
        panic!("{}", ("palette must be 256*3 bytes").to_string());
    }
    let mut frame_lists: Vec<Vec<i64>> = vec![];
    for fr in (frames).iter().cloned() {
        let mut fr_list: Vec<i64> = vec![];
        for v in fr {
            fr_list.push(((v) as i64));
        }
        if fr_list.len() as i64 != width * height {
            panic!("{}", ("frame size mismatch").to_string());
        }
        frame_lists.push(fr_list);
    }
    let mut palette_list: Vec<i64> = vec![];
    for v in palette {
        palette_list.push(((v) as i64));
    }
    let mut out: Vec<i64> = vec![];
    _gif_append_list((out).clone(), &(vec![71, 73, 70, 56, 57, 97]));
    _gif_append_list((out).clone(), &(_gif_u16le(width)));
    _gif_append_list((out).clone(), &(_gif_u16le(height)));
    out.push(0xF7);
    out.push(0);
    out.push(0);
    _gif_append_list((out).clone(), &(palette_list));
    
    _gif_append_list((out).clone(), &(vec![0x21, 0xFF, 0x0B, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 0x03, 0x01]));
    _gif_append_list((out).clone(), &(_gif_u16le(py_loop)));
    out.push(0);
    
    for fr_list in (frame_lists).iter().cloned() {
        _gif_append_list((out).clone(), &(vec![0x21, 0xF9, 0x04, 0x00]));
        _gif_append_list((out).clone(), &(_gif_u16le(delay_cs)));
        _gif_append_list((out).clone(), &(vec![0x00, 0x00]));
        
        out.push(0x2C);
        _gif_append_list((out).clone(), &(_gif_u16le(0)));
        _gif_append_list((out).clone(), &(_gif_u16le(0)));
        _gif_append_list((out).clone(), &(_gif_u16le(width)));
        _gif_append_list((out).clone(), &(_gif_u16le(height)));
        out.push(0);
        out.push(8);
        let compressed = _lzw_encode(&((fr_list).clone()), 8);
        let mut pos = 0;
        while pos < compressed.len() as i64 {
            let remain = compressed.len() as i64 - pos;
            let chunk_len = (if remain > 255 { 255 } else { remain });
            out.push(chunk_len);
            let mut i = 0;
            while i < chunk_len {
                out.push(((compressed[((pos + i) as usize)]) as i64));
                i += 1;
            }
            pos += chunk_len;
        }
        out.push(0);
    }
    out.push(0x3B);
    
    let f = open(path, ("wb").to_string());
    {
        f.write((out).clone());
    }
    {
        f.close();
    }
}

fn main() {
    ("アニメーションGIFを書き出すための最小ヘルパー。").to_string();
}
