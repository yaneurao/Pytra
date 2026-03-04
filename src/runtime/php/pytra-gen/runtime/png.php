<?php
// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: tools/gen_image_runtime_from_canonical.py
declare(strict_types=1);

function __pytra_png_u16le(int $v): string {
    $x = $v & 0xFFFF;
    return chr($x & 0xFF) . chr(($x >> 8) & 0xFF);
}

function __pytra_png_u32be(int $v): string {
    $x = $v & 0xFFFFFFFF;
    return chr(($x >> 24) & 0xFF)
        . chr(($x >> 16) & 0xFF)
        . chr(($x >> 8) & 0xFF)
        . chr($x & 0xFF);
}

function __pytra_png_crc32(string $data): int {
    $crc = 0xFFFFFFFF;
    $poly = 0xEDB88320;
    $n = strlen($data);
    $i = 0;
    while ($i < $n) {
        $crc = ($crc ^ ord($data[$i])) & 0xFFFFFFFF;
        $bit = 0;
        while ($bit < 8) {
            if (($crc & 1) !== 0) {
                $crc = (($crc >> 1) ^ $poly) & 0xFFFFFFFF;
            } else {
                $crc = ($crc >> 1) & 0xFFFFFFFF;
            }
            $bit += 1;
        }
        $i += 1;
    }
    return ($crc ^ 0xFFFFFFFF) & 0xFFFFFFFF;
}

function __pytra_png_adler32(string $data): int {
    $mod = 65521;
    $s1 = 1;
    $s2 = 0;
    $n = strlen($data);
    $i = 0;
    while ($i < $n) {
        $s1 += ord($data[$i]);
        if ($s1 >= $mod) {
            $s1 -= $mod;
        }
        $s2 += $s1;
        $s2 %= $mod;
        $i += 1;
    }
    return (($s2 << 16) | $s1) & 0xFFFFFFFF;
}

function __pytra_png_to_bytes($v): string {
    if (is_string($v)) {
        return $v;
    }
    if (!is_array($v)) {
        return '';
    }
    if (count($v) === 0) {
        return '';
    }
    $out = '';
    $chunk = [];
    foreach ($v as $item) {
        $chunk[] = ((int)$item) & 0xFF;
        if (count($chunk) >= 4096) {
            $out .= pack('C*', ...$chunk);
            $chunk = [];
        }
    }
    if (count($chunk) > 0) {
        $out .= pack('C*', ...$chunk);
    }
    return $out;
}

function __pytra_png_zlib_store(string $data): string {
    $out = "\x78\x01";
    $n = strlen($data);
    $pos = 0;
    while ($pos < $n) {
        $remain = $n - $pos;
        $chunkLen = $remain > 65535 ? 65535 : $remain;
        $final = (($pos + $chunkLen) >= $n) ? 1 : 0;
        $out .= chr($final);
        $out .= __pytra_png_u16le($chunkLen);
        $out .= __pytra_png_u16le(0xFFFF ^ $chunkLen);
        $out .= substr($data, $pos, $chunkLen);
        $pos += $chunkLen;
    }
    $out .= __pytra_png_u32be(__pytra_png_adler32($data));
    return $out;
}

function __pytra_png_chunk(string $chunkType, string $payload): string {
    $crc = __pytra_png_crc32($chunkType . $payload);
    return __pytra_png_u32be(strlen($payload))
        . $chunkType
        . $payload
        . __pytra_png_u32be($crc);
}

function __pytra_write_rgb_png($_path, $_width, $_height, $_pixels) {
    $path = (string)$_path;
    $width = (int)$_width;
    $height = (int)$_height;
    $raw = __pytra_png_to_bytes($_pixels);
    $expected = $width * $height * 3;
    if (strlen($raw) !== $expected) {
        throw new InvalidArgumentException(
            'pixels length mismatch: got=' . strlen($raw) . ' expected=' . $expected
        );
    }

    $rowBytes = $width * 3;
    $scanlines = [];
    $y = 0;
    while ($y < $height) {
        $start = $y * $rowBytes;
        $scanlines[] = "\x00";
        $scanlines[] = substr($raw, $start, $rowBytes);
        $y += 1;
    }
    $scanlineRaw = implode('', $scanlines);

    $ihdr = __pytra_png_u32be($width)
        . __pytra_png_u32be($height)
        . "\x08\x02\x00\x00\x00";
    $idat = __pytra_png_zlib_store($scanlineRaw);
    $png = "\x89PNG\r\n\x1A\n"
        . __pytra_png_chunk("IHDR", $ihdr)
        . __pytra_png_chunk("IDAT", $idat)
        . __pytra_png_chunk("IEND", "");

    file_put_contents($path, $png);
    return null;
}
