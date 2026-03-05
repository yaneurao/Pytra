// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_runtime_from_manifest.py

function _lzw_encode(data, min_code_size) {
    if ((data).length === 0) {
        return "";
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
        bit_buffer >>= 8;
        bit_count -= 8;
    }
    code_size = min_code_size + 1;
    
    for (const v of data) {
        bit_buffer |= v << bit_count;
        bit_count += code_size;
        while (bit_count >= 8) {
            out.push(bit_buffer & 0xFF);
            bit_buffer >>= 8;
            bit_count -= 8;
        }
        bit_buffer |= clear_code << bit_count;
        bit_count += code_size;
        while (bit_count >= 8) {
            out.push(bit_buffer & 0xFF);
            bit_buffer >>= 8;
            bit_count -= 8;
        }
        code_size = min_code_size + 1;
    }
    bit_buffer |= end_code << bit_count;
    bit_count += code_size;
    while (bit_count >= 8) {
        out.push(bit_buffer & 0xFF);
        bit_buffer >>= 8;
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
    for (const fr of frames) {
        if ((fr).length !== width * height) {
            throw new Error("frame size mismatch");
        }
    }
    let out = [];
    out = out.concat("GIF89a");
    out = out.concat(width.to_bytes(2, "little"));
    out = out.concat(height.to_bytes(2, "little"));
    out.push(0xF7);
    out.push(0);
    out.push(0);
    out = out.concat(palette);
    
    // Netscape loop extension
    out = out.concat("x21xFFx0BNETSCAPE2.0x03x01");
    out = out.concat(loop.to_bytes(2, "little"));
    out.push(0);
    
    for (const fr of frames) {
        out = out.concat("x21xF9x04x00");
        out = out.concat(delay_cs.to_bytes(2, "little"));
        out = out.concat("x00x00");
        
        out.push(0x2C);
        out = out.concat((0).to_bytes(2, "little"));
        out = out.concat((0).to_bytes(2, "little"));
        out = out.concat(width.to_bytes(2, "little"));
        out = out.concat(height.to_bytes(2, "little"));
        out.push(0);
        
        out.push(8);
        let compressed = _lzw_encode(fr, 8);
        let pos = 0;
        while (pos < (compressed).length) {
            let chunk = compressed.slice(pos, pos + 255);
            out.push((chunk).length);
            out = out.concat(chunk);
            pos += (chunk).length;
        }
        out.push(0);
    }
    out.push(0x3B);
    
    let f = open(path, "wb");
    try {
        f.write(out);
    } finally {
        f.close();
    }
}

"アニメーションGIFを書き出すための最小ヘルパー。";

module.exports = {grayscale_palette, save_gif};
