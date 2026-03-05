// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
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

function _png_append_list(dst, src) {
    let i = 0;
    let n = (src).length;
    while (i < n) {
        dst.push(src[(((i) < 0) ? ((src).length + (i)) : (i))]);
        i += 1;
    }
}

function _crc32(data) {
    let crc = 0xFFFFFFFF;
    let poly = 0xEDB88320;
    for (const b of data) {
        crc = crc ^ b;
        let i = 0;
        while (i < 8) {
            let lowbit = crc & 1;
            if (lowbit !== 0) {
                crc = crc >>> 1 ^ poly;
            } else {
                crc = crc >>> 1;
            }
            i += 1;
        }
    }
    return crc ^ 0xFFFFFFFF;
}

function _adler32(data) {
    let mod = 65521;
    let s1 = 1;
    let s2 = 0;
    for (const b of data) {
        s1 += b;
        if (s1 >= mod) {
            s1 -= mod;
        }
        s2 += s1;
        s2 = s2 % mod;
    }
    return (s2 << 16 | s1) & 0xFFFFFFFF;
}

function _png_u16le(v) {
    return [v & 0xFF, v >>> 8 & 0xFF];
}

function _png_u32be(v) {
    return [v >>> 24 & 0xFF, v >>> 16 & 0xFF, v >>> 8 & 0xFF, v & 0xFF];
}

function _zlib_deflate_store(data) {
    let out = [];
    _png_append_list(out, [0x78, 0x01]);
    let n = (data).length;
    let pos = 0;
    while (pos < n) {
        let remain = n - pos;
        let chunk_len = (remain > 65535 ? 65535 : remain);
        let final = (pos + chunk_len >= n ? 1 : 0);
        out.push(final);
        _png_append_list(out, _png_u16le(chunk_len));
        _png_append_list(out, _png_u16le(0xFFFF ^ chunk_len));
        let i = pos;
        let end = pos + chunk_len;
        while (i < end) {
            out.push(data[(((i) < 0) ? ((data).length + (i)) : (i))]);
            i += 1;
        }
        pos += chunk_len;
    }
    _png_append_list(out, _png_u32be(_adler32(data)));
    return out;
}

function _chunk(chunk_type, data) {
    let crc_input = [];
    _png_append_list(crc_input, chunk_type);
    _png_append_list(crc_input, data);
    let crc = _crc32(crc_input) & 0xFFFFFFFF;
    let out = [];
    _png_append_list(out, _png_u32be((data).length));
    _png_append_list(out, chunk_type);
    _png_append_list(out, data);
    _png_append_list(out, _png_u32be(crc));
    return out;
}

function write_rgb_png(path, width, height, pixels) {
    let raw = [];
    for (const b of pixels) {
        raw.push(Math.trunc(Number(b)));
    }
    let expected = width * height * 3;
    if ((raw).length !== expected) {
        throw new Error("pixels length mismatch: got=" + String((raw).length) + " expected=" + String(expected));
    }
    let scanlines = [];
    let row_bytes = width * 3;
    let y = 0;
    while (y < height) {
        scanlines.push(0);
        let start = y * row_bytes;
        let end = start + row_bytes;
        let i = start;
        while (i < end) {
            scanlines.push(raw[(((i) < 0) ? ((raw).length + (i)) : (i))]);
            i += 1;
        }
        y += 1;
    }
    let ihdr = [];
    _png_append_list(ihdr, _png_u32be(width));
    _png_append_list(ihdr, _png_u32be(height));
    _png_append_list(ihdr, [8, 2, 0, 0, 0]);
    let idat = _zlib_deflate_store(scanlines);
    
    let png = [];
    _png_append_list(png, [137, 80, 78, 71, 13, 10, 26, 10]);
    _png_append_list(png, _chunk([73, 72, 68, 82], ihdr));
    _png_append_list(png, _chunk([73, 68, 65, 84], idat));
    let iend_data = [];
    _png_append_list(png, _chunk([73, 69, 78, 68], iend_data));
    
    let f = open(path, "wb");
    try {
        f.write((Array.isArray((png)) ? (png).slice() : Array.from((png))));
    } finally {
        f.close();
    }
}

module.exports = {write_rgb_png};
