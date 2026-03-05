<?php
declare(strict_types=1);

function __pytra_gif_u16le(int $v): string {
    $x = $v & 0xFFFF;
    return chr($x & 0xFF) . chr(($x >> 8) & 0xFF);
}

function __pytra_gif_to_bytes($v): string {
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

function __pytra_gif_emit_code(string &$out, int &$bitBuffer, int &$bitCount, int $code, int $bits): void {
    $bitBuffer |= ($code << $bitCount);
    $bitCount += $bits;
    while ($bitCount >= 8) {
        $out .= chr($bitBuffer & 0xFF);
        $bitBuffer >>= 8;
        $bitCount -= 8;
    }
}

function __pytra_gif_lzw_encode(string $data, int $minCodeSize = 8): string {
    $n = strlen($data);
    if ($n === 0) {
        return '';
    }

    $clearCode = 1 << $minCodeSize;
    $endCode = $clearCode + 1;
    $codeSize = $minCodeSize + 1;
    $out = '';
    $bitBuffer = 0;
    $bitCount = 0;

    __pytra_gif_emit_code($out, $bitBuffer, $bitCount, $clearCode, $codeSize);
    $i = 0;
    while ($i < $n) {
        __pytra_gif_emit_code($out, $bitBuffer, $bitCount, ord($data[$i]), $codeSize);
        __pytra_gif_emit_code($out, $bitBuffer, $bitCount, $clearCode, $codeSize);
        $i += 1;
    }
    __pytra_gif_emit_code($out, $bitBuffer, $bitCount, $endCode, $codeSize);
    if ($bitCount > 0) {
        $out .= chr($bitBuffer & 0xFF);
    }
    return $out;
}

function __pytra_save_gif($_path, $_width, $_height, $_frames, $_palette = [], $_delay_cs = 4, $_loop = 0) {
    $path = (string)$_path;
    $width = (int)$_width;
    $height = (int)$_height;
    $delayCs = (int)$_delay_cs;
    $loop = (int)$_loop;

    $palette = __pytra_gif_to_bytes($_palette);
    if (strlen($palette) !== 256 * 3) {
        throw new InvalidArgumentException('palette must be 256*3 bytes');
    }

    $framePixels = $width * $height;
    $frames = is_array($_frames) ? array_values($_frames) : [];
    $normalizedFrames = [];
    foreach ($frames as $frame) {
        $fr = __pytra_gif_to_bytes($frame);
        if (strlen($fr) !== $framePixels) {
            throw new InvalidArgumentException('frame size mismatch');
        }
        $normalizedFrames[] = $fr;
    }

    $out = "GIF89a";
    $out .= __pytra_gif_u16le($width);
    $out .= __pytra_gif_u16le($height);
    $out .= "\xF7";  // GCT flag=1, color resolution=7, table size=7 (256).
    $out .= "\x00";  // background color index.
    $out .= "\x00";  // pixel aspect ratio.
    $out .= $palette;

    // Netscape loop extension.
    $out .= "\x21\xFF\x0BNETSCAPE2.0\x03\x01";
    $out .= __pytra_gif_u16le($loop);
    $out .= "\x00";

    foreach ($normalizedFrames as $fr) {
        $out .= "\x21\xF9\x04\x00";
        $out .= __pytra_gif_u16le($delayCs);
        $out .= "\x00\x00";

        $out .= "\x2C";
        $out .= __pytra_gif_u16le(0);
        $out .= __pytra_gif_u16le(0);
        $out .= __pytra_gif_u16le($width);
        $out .= __pytra_gif_u16le($height);
        $out .= "\x00";

        $out .= "\x08";
        $compressed = __pytra_gif_lzw_encode($fr, 8);
        $n = strlen($compressed);
        $pos = 0;
        while ($pos < $n) {
            $chunk = substr($compressed, $pos, 255);
            $chunkLen = strlen($chunk);
            $out .= chr($chunkLen);
            $out .= $chunk;
            $pos += $chunkLen;
        }
        $out .= "\x00";
    }

    $out .= "\x3B";
    file_put_contents($path, $out);
    return null;
}
