// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: tools/gen_runtime_from_manifest.py

function _crc32(data) {
    let crc = 0xFFFFFFFF;
    let poly = 0xEDB88320;
    for (const b of data) {
        crc ^= b;
        let i = 0;
        while (i < 8) {
            if (crc & 1 !== 0) {
                crc = crc >> 1 ^ poly;
            } else {
                crc >>= 1;
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
        s2 %= mod;
    }
    return (s2 << 16 | s1) & 0xFFFFFFFF;
}

function _u16le(v) {
    return (Array.isArray(([v & 0xFF, v >> 8 & 0xFF])) ? ([v & 0xFF, v >> 8 & 0xFF]).slice() : Array.from(([v & 0xFF, v >> 8 & 0xFF])));
}

function _u32be(v) {
    return (Array.isArray(([v >> 24 & 0xFF, v >> 16 & 0xFF, v >> 8 & 0xFF, v & 0xFF])) ? ([v >> 24 & 0xFF, v >> 16 & 0xFF, v >> 8 & 0xFF, v & 0xFF]).slice() : Array.from(([v >> 24 & 0xFF, v >> 16 & 0xFF, v >> 8 & 0xFF, v & 0xFF])));
}

function _zlib_deflate_store(data) {
    let out = [];
    // zlib header: CMF=0x78(Deflate, 32K window), FLG=0x01(check bits OK, fastest)
    out.extend((Array.isArray(([0x78, 0x01])) ? ([0x78, 0x01]).slice() : Array.from(([0x78, 0x01]))));
    let n = (data).length;
    let pos = 0;
    while (pos < n) {
        let remain = n - pos;
        let chunk_len = (remain > 65535 ? 65535 : remain);
        let final = (pos + chunk_len >= n ? 1 : 0);
        // stored block: BTYPE=00, header bit field in LSB order (final in bit0)
        out.push(final);
        out.extend(_u16le(chunk_len));
        out.extend(_u16le(0xFFFF ^ chunk_len));
        out.extend(data.slice(pos, pos + chunk_len));
        pos += chunk_len;
    }
    out.extend(_u32be(_adler32(data)));
    return (Array.isArray((out)) ? (out).slice() : Array.from((out)));
}

function _chunk(chunk_type, data) {
    let length = _u32be((data).length);
    let crc = _crc32(chunk_type + data) & 0xFFFFFFFF;
    return length + chunk_type + data + _u32be(crc);
}

function write_rgb_png(path, width, height, pixels) {
    let raw = (Array.isArray((pixels)) ? (pixels).slice() : Array.from((pixels)));
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
        scanlines.extend(raw.slice(start, end));
        y += 1;
    }
    let ihdr = _u32be(width) + _u32be(height) + (Array.isArray(([8, 2, 0, 0, 0])) ? ([8, 2, 0, 0, 0]).slice() : Array.from(([8, 2, 0, 0, 0])));
    let idat = _zlib_deflate_store((Array.isArray((scanlines)) ? (scanlines).slice() : Array.from((scanlines))));
    
    let png = [];
    png.extend((Array.isArray(([137, 80, 78, 71, 13, 10, 26, 10])) ? ([137, 80, 78, 71, 13, 10, 26, 10]).slice() : Array.from(([137, 80, 78, 71, 13, 10, 26, 10]))));
    png.extend(_chunk((Array.isArray(([73, 72, 68, 82])) ? ([73, 72, 68, 82]).slice() : Array.from(([73, 72, 68, 82]))), ihdr));
    png.extend(_chunk((Array.isArray(([73, 68, 65, 84])) ? ([73, 68, 65, 84]).slice() : Array.from(([73, 68, 65, 84]))), idat));
    png.extend(_chunk((Array.isArray(([73, 69, 78, 68])) ? ([73, 69, 78, 68]).slice() : Array.from(([73, 69, 78, 68]))), ""));
    
    let f = open(path, "wb");
    try {
        f.write(png);
    } finally {
        f.close();
    }
}

"PNG 書き出しユーティリティ（Python実行用）。\n\nこのモジュールは sample/py のスクリプトから利用し、\nRGB 8bit バッファを PNG ファイルとして保存する。\n";
