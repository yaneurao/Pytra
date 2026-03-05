// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_runtime_from_manifest.py

const fs = require('node:fs');
const path = require('node:path');
function open(pathLike, mode) {
    const filePath = String(pathLike);
    const writeMode = String(mode || 'wb');
    return {
        write(data) {
            const bytes = Array.isArray(data) ? data : Array.from(data || []);
            fs.mkdirSync(path.dirname(filePath), { recursive: true });
            const flag = (writeMode === 'ab' || writeMode === 'a') ? 'a' : 'w';
            fs.writeFileSync(filePath, Buffer.from(bytes), { flag });
        },
        close() {},
    };
}

function _gif_append_list(dst, src) {
    let i = 0;
    let n = (src).length;
    while (i < n) {
        dst.push(src[(((i) < 0) ? ((src).length + (i)) : (i))]);
        i += 1;
    }
}

function _gif_u16le(v) {
    return [v & 0xFF, v >>> 8 & 0xFF];
}

function _lzw_encode(data, min_code_size) {
    if ((data).length === 0) {
        return (Array.isArray(([])) ? ([]).slice() : Array.from(([])));
    }
    let clear_code = 1 << min_code_size;
    let end_code = clear_code + 1;
    let code_size = min_code_size + 1;
    
    let out = [];
    let bit_buffer = 0;
    let bit_count = 0;
    
    bit_buffer |= clear_code << bit_count;
    bit_count += code_size;
    while (bit_count >= 8) {
        out.push(bit_buffer & 0xFF);
        bit_buffer = bit_buffer >>> 8;
        bit_count -= 8;
    }
    code_size = min_code_size + 1;
    
    for (const v of data) {
        bit_buffer |= v << bit_count;
        bit_count += code_size;
        while (bit_count >= 8) {
            out.push(bit_buffer & 0xFF);
            bit_buffer = bit_buffer >>> 8;
            bit_count -= 8;
        }
        bit_buffer |= clear_code << bit_count;
        bit_count += code_size;
        while (bit_count >= 8) {
            out.push(bit_buffer & 0xFF);
            bit_buffer = bit_buffer >>> 8;
            bit_count -= 8;
        }
        code_size = min_code_size + 1;
    }
    bit_buffer |= end_code << bit_count;
    bit_count += code_size;
    while (bit_count >= 8) {
        out.push(bit_buffer & 0xFF);
        bit_buffer = bit_buffer >>> 8;
        bit_count -= 8;
    }
    if (bit_count > 0) {
        out.push(bit_buffer & 0xFF);
    }
    return (Array.isArray((out)) ? (out).slice() : Array.from((out)));
}

function grayscale_palette() {
    let p = [];
    let i = 0;
    while (i < 256) {
        p.push(i);
        p.push(i);
        p.push(i);
        i += 1;
    }
    return (Array.isArray((p)) ? (p).slice() : Array.from((p)));
}

function save_gif(path, width, height, frames, palette, delay_cs, loop) {
    if ((palette).length !== 256 * 3) {
        throw new Error("palette must be 256*3 bytes");
    }
    let frame_lists = [];
    for (const fr of frames) {
        let fr_list = [];
        for (const v of fr) {
            fr_list.push(Math.trunc(Number(v)));
        }
        if ((fr_list).length !== width * height) {
            throw new Error("frame size mismatch");
        }
        frame_lists.push(fr_list);
    }
    let palette_list = [];
    for (const v of palette) {
        palette_list.push(Math.trunc(Number(v)));
    }
    let out = [];
    _gif_append_list(out, [71, 73, 70, 56, 57, 97]);
    _gif_append_list(out, _gif_u16le(width));
    _gif_append_list(out, _gif_u16le(height));
    out.push(0xF7);
    out.push(0);
    out.push(0);
    _gif_append_list(out, palette_list);
    
    _gif_append_list(out, [0x21, 0xFF, 0x0B, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 0x03, 0x01]);
    _gif_append_list(out, _gif_u16le(loop));
    out.push(0);
    
    for (const fr_list of frame_lists) {
        _gif_append_list(out, [0x21, 0xF9, 0x04, 0x00]);
        _gif_append_list(out, _gif_u16le(delay_cs));
        _gif_append_list(out, [0x00, 0x00]);
        
        out.push(0x2C);
        _gif_append_list(out, _gif_u16le(0));
        _gif_append_list(out, _gif_u16le(0));
        _gif_append_list(out, _gif_u16le(width));
        _gif_append_list(out, _gif_u16le(height));
        out.push(0);
        out.push(8);
        let compressed = _lzw_encode((Array.isArray((fr_list)) ? (fr_list).slice() : Array.from((fr_list))), 8);
        let pos = 0;
        while (pos < (compressed).length) {
            let remain = (compressed).length - pos;
            let chunk_len = (remain > 255 ? 255 : remain);
            out.push(chunk_len);
            let i = 0;
            while (i < chunk_len) {
                out.push(compressed[(((pos + i) < 0) ? ((compressed).length + (pos + i)) : (pos + i))]);
                i += 1;
            }
            pos += chunk_len;
        }
        out.push(0);
    }
    out.push(0x3B);
    
    let f = open(path, "wb");
    try {
        f.write((Array.isArray((out)) ? (out).slice() : Array.from((out))));
    } finally {
        f.close();
    }
}

module.exports = {grayscale_palette, save_gif};
