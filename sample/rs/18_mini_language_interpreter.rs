use crate::time::perf_counter;

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

#[derive(Clone, Debug)]
struct Token {
    kind: String,
    text: String,
    pos: i64,
}
impl Token {
    fn new(kind: String, text: String, pos: i64) -> Self {
        Self {
            kind: kind,
            text: text,
            pos: pos,
        }
    }
}

#[derive(Clone, Debug)]
struct ExprNode {
    kind: String,
    value: i64,
    name: String,
    op: String,
    left: i64,
    right: i64,
}
impl ExprNode {
    fn new(kind: String, value: i64, name: String, op: String, left: i64, right: i64) -> Self {
        Self {
            kind: kind,
            value: value,
            name: name,
            op: op,
            left: left,
            right: right,
        }
    }
}

#[derive(Clone, Debug)]
struct StmtNode {
    kind: String,
    name: String,
    expr_index: i64,
}
impl StmtNode {
    fn new(kind: String, name: String, expr_index: i64) -> Self {
        Self {
            kind: kind,
            name: name,
            expr_index: expr_index,
        }
    }
}

fn tokenize(lines: &Vec<String>) -> Vec<Token> {
    let mut tokens: Vec<Token> = vec![];
    for (line_index, source) in (lines).iter().enumerate().map(|(i, v)| (i as i64, v)) {
        let mut i: i64 = 0;
        let n: i64 = source.len() as i64;
        while i < n {
            let ch: String = ((py_str_at(&source, ((i) as i64))).to_string());
            
            if ch == " " {
                i += 1;
                continue;
            }
            if ch == "+" {
                tokens.push(Token::new(("PLUS").to_string(), ((ch).to_string()), i));
                i += 1;
                continue;
            }
            if ch == "-" {
                tokens.push(Token::new(("MINUS").to_string(), ((ch).to_string()), i));
                i += 1;
                continue;
            }
            if ch == "*" {
                tokens.push(Token::new(("STAR").to_string(), ((ch).to_string()), i));
                i += 1;
                continue;
            }
            if ch == "/" {
                tokens.push(Token::new(("SLASH").to_string(), ((ch).to_string()), i));
                i += 1;
                continue;
            }
            if ch == "(" {
                tokens.push(Token::new(("LPAREN").to_string(), ((ch).to_string()), i));
                i += 1;
                continue;
            }
            if ch == ")" {
                tokens.push(Token::new(("RPAREN").to_string(), ((ch).to_string()), i));
                i += 1;
                continue;
            }
            if ch == "=" {
                tokens.push(Token::new(("EQUAL").to_string(), ((ch).to_string()), i));
                i += 1;
                continue;
            }
            if py_isdigit(&ch) {
                let mut start: i64 = i;
                while (i < n) && py_isdigit(&py_str_at(&source, ((i) as i64))) {
                    i += 1;
                }
                let mut text: String = ((py_slice_str(&source, Some((start) as i64), Some((i) as i64))).to_string());
                tokens.push(Token::new(("NUMBER").to_string(), ((text).to_string()), start));
                continue;
            }
            if py_isalpha(&ch) || (ch == "_") {
                let mut start = i;
                while (i < n) && ((py_isalpha(&py_str_at(&source, ((i) as i64))) || (py_str_at(&source, ((i) as i64)) == "_")) || py_isdigit(&py_str_at(&source, ((i) as i64)))) {
                    i += 1;
                }
                let mut text = py_slice_str(&source, Some((start) as i64), Some((i) as i64));
                if text == "let" {
                    tokens.push(Token::new(("LET").to_string(), ((text).to_string()), start));
                } else {
                    if text == "print" {
                        tokens.push(Token::new(("PRINT").to_string(), ((text).to_string()), start));
                    } else {
                        tokens.push(Token::new(("IDENT").to_string(), ((text).to_string()), start));
                    }
                }
                continue;
            }
            panic!("{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", ("tokenize error at line=").to_string(), (line_index).to_string()), (" pos=").to_string()), (i).to_string()), (" ch=").to_string()), ch));
        }
        tokens.push(Token::new(("NEWLINE").to_string(), ("").to_string(), n));
    }
    tokens.push(Token::new(("EOF").to_string(), ("").to_string(), lines.len() as i64));
    return tokens;
}

#[derive(Clone, Debug)]
struct Parser {
    tokens: Vec<Token>,
    pos: i64,
    expr_nodes: Vec<ExprNode>,
}
impl Parser {
    fn new(tokens: Vec<Token>) -> Self {
        Self {
            tokens: tokens,
            pos: 0,
            expr_nodes: Vec::new(),
        }
    }
    
    fn new_expr_nodes(&self) -> Vec<ExprNode> {
        return vec![];
    }
    
    fn peek_kind(&self) -> String {
        return (self.tokens[((if ((self.pos) as i64) < 0 { (self.tokens.len() as i64 + ((self.pos) as i64)) } else { ((self.pos) as i64) }) as usize)].kind).clone();
    }
    
    fn py_match(&mut self, kind: &str) -> bool {
        if self.peek_kind() == kind {
            self.pos += 1;
            return true;
        }
        return false;
    }
    
    fn expect(&mut self, kind: &str) -> Token {
        if self.peek_kind() != kind {
            let t: Token = (self.tokens[((if ((self.pos) as i64) < 0 { (self.tokens.len() as i64 + ((self.pos) as i64)) } else { ((self.pos) as i64) }) as usize)]).clone();
            panic!("{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", ("parse error at pos=").to_string(), py_any_to_string(&t.pos)), (", expected=").to_string()), kind), (", got=").to_string()), t.kind));
        }
        let token: Token = (self.tokens[((if ((self.pos) as i64) < 0 { (self.tokens.len() as i64 + ((self.pos) as i64)) } else { ((self.pos) as i64) }) as usize)]).clone();
        self.pos += 1;
        return token;
    }
    
    fn skip_newlines(&mut self) {
        while self.py_match("NEWLINE") {
            ();
        }
    }
    
    fn add_expr(&mut self, node: ExprNode) -> i64 {
        self.expr_nodes.push(node);
        return self.expr_nodes.len() as i64 - 1;
    }
    
    fn parse_program(&mut self) -> Vec<StmtNode> {
        let mut stmts: Vec<StmtNode> = vec![];
        self.skip_newlines();
        while self.peek_kind() != "EOF" {
            let stmt: StmtNode = self.parse_stmt();
            stmts.push(stmt);
            self.skip_newlines();
        }
        return stmts;
    }
    
    fn parse_stmt(&mut self) -> StmtNode {
        if self.py_match("LET") {
            let let_name: String = ((py_any_to_string(&self.expect("IDENT").text)).to_string());
            self.expect("EQUAL");
            let let_expr_index: i64 = self.parse_expr();
            return StmtNode::new(("let").to_string(), ((let_name).to_string()), let_expr_index);
        }
        if self.py_match("PRINT") {
            let print_expr_index: i64 = self.parse_expr();
            return StmtNode::new(("print").to_string(), ("").to_string(), print_expr_index);
        }
        let assign_name: String = ((py_any_to_string(&self.expect("IDENT").text)).to_string());
        self.expect("EQUAL");
        let assign_expr_index: i64 = self.parse_expr();
        return StmtNode::new(("assign").to_string(), ((assign_name).to_string()), assign_expr_index);
    }
    
    fn parse_expr(&mut self) -> i64 {
        return self.parse_add();
    }
    
    fn parse_add(&mut self) -> i64 {
        let mut left: i64 = self.parse_mul();
        while true {
            if self.py_match("PLUS") {
                let mut right: i64 = self.parse_mul();
                left = self.add_expr(ExprNode::new(("bin").to_string(), 0, ("").to_string(), ("+").to_string(), left, right));
                continue;
            }
            if self.py_match("MINUS") {
                let mut right = self.parse_mul();
                left = self.add_expr(ExprNode::new(("bin").to_string(), 0, ("").to_string(), ("-").to_string(), left, right));
                continue;
            }
            break;
        }
        return left;
    }
    
    fn parse_mul(&mut self) -> i64 {
        let mut left: i64 = self.parse_unary();
        while true {
            if self.py_match("STAR") {
                let mut right: i64 = self.parse_unary();
                left = self.add_expr(ExprNode::new(("bin").to_string(), 0, ("").to_string(), ("*").to_string(), left, right));
                continue;
            }
            if self.py_match("SLASH") {
                let mut right = self.parse_unary();
                left = self.add_expr(ExprNode::new(("bin").to_string(), 0, ("").to_string(), ("/").to_string(), left, right));
                continue;
            }
            break;
        }
        return left;
    }
    
    fn parse_unary(&mut self) -> i64 {
        if self.py_match("MINUS") {
            let child: i64 = self.parse_unary();
            return self.add_expr(ExprNode::new(("neg").to_string(), 0, ("").to_string(), ("").to_string(), child, -1));
        }
        return self.parse_primary();
    }
    
    fn parse_primary(&mut self) -> i64 {
        if self.py_match("NUMBER") {
            let token_num: Token = (self.tokens[((if ((self.pos - 1) as i64) < 0 { (self.tokens.len() as i64 + ((self.pos - 1) as i64)) } else { ((self.pos - 1) as i64) }) as usize)]).clone();
            return self.add_expr(ExprNode::new(("lit").to_string(), ((token_num.text).parse::<i64>().unwrap_or(0)), ("").to_string(), ("").to_string(), -1, -1));
        }
        if self.py_match("IDENT") {
            let token_ident: Token = (self.tokens[((if ((self.pos - 1) as i64) < 0 { (self.tokens.len() as i64 + ((self.pos - 1) as i64)) } else { ((self.pos - 1) as i64) }) as usize)]).clone();
            return self.add_expr(ExprNode::new(("var").to_string(), 0, ((token_ident.text).to_string()), ("").to_string(), -1, -1));
        }
        if self.py_match("LPAREN") {
            let expr_index: i64 = self.parse_expr();
            self.expect("RPAREN");
            return expr_index;
        }
        let t = (self.tokens[((if ((self.pos) as i64) < 0 { (self.tokens.len() as i64 + ((self.pos) as i64)) } else { ((self.pos) as i64) }) as usize)]).clone();
        panic!("{}", format!("{}{}", format!("{}{}", format!("{}{}", ("primary parse error at pos=").to_string(), py_any_to_string(&t.pos)), (" got=").to_string()), t.kind));
    }
}

fn eval_expr(expr_index: i64, expr_nodes: &Vec<ExprNode>, env: &::std::collections::BTreeMap<String, i64>) -> i64 {
    let node: ExprNode = (expr_nodes[((if ((expr_index) as i64) < 0 { (expr_nodes.len() as i64 + ((expr_index) as i64)) } else { ((expr_index) as i64) }) as usize)]).clone();
    
    if node.kind == "lit" {
        return node.value;
    }
    if node.kind == "var" {
        if !((env.contains_key(&node.name))) {
            panic!("{}", format!("{}{}", ("undefined variable: ").to_string(), node.name));
        }
        return env.get(&node.name).cloned().expect("dict key not found");
    }
    if node.kind == "neg" {
        return -eval_expr(node.left, expr_nodes, env);
    }
    if node.kind == "bin" {
        let lhs: i64 = eval_expr(node.left, expr_nodes, env);
        let rhs: i64 = eval_expr(node.right, expr_nodes, env);
        if node.op == "+" {
            return lhs + rhs;
        }
        if node.op == "-" {
            return lhs - rhs;
        }
        if node.op == "*" {
            return lhs * rhs;
        }
        if node.op == "/" {
            if rhs == 0 {
                panic!("{}", ("division by zero").to_string());
            }
            return lhs / rhs;
        }
        panic!("{}", format!("{}{}", ("unknown operator: ").to_string(), node.op));
    }
    panic!("{}", format!("{}{}", ("unknown node kind: ").to_string(), node.kind));
}

fn execute(stmts: &Vec<StmtNode>, expr_nodes: &Vec<ExprNode>, trace: bool) -> i64 {
    let mut env: ::std::collections::BTreeMap<String, i64> = ::std::collections::BTreeMap::from([]);
    let mut checksum: i64 = 0;
    let mut printed: i64 = 0;
    
    for stmt in (stmts).iter() {
        if stmt.kind == "let" {
            env.insert(((stmt.name).to_string()), eval_expr(stmt.expr_index, expr_nodes, &(env)));
            continue;
        }
        if stmt.kind == "assign" {
            if !((env.contains_key(&stmt.name))) {
                panic!("{}", format!("{}{}", ("assign to undefined variable: ").to_string(), stmt.name));
            }
            env.insert(((stmt.name).to_string()), eval_expr(stmt.expr_index, expr_nodes, &(env)));
            continue;
        }
        let value: i64 = eval_expr(stmt.expr_index, expr_nodes, &(env));
        if trace {
            println!("{}", value);
        }
        let mut norm: i64 = value % 1000000007;
        if norm < 0 {
            norm += 1000000007;
        }
        checksum = (checksum * 131 + norm) % 1000000007;
        printed += 1;
    }
    if trace {
        println!("{} {}", ("printed:").to_string(), printed);
    }
    return checksum;
}

fn build_benchmark_source(var_count: i64, loops: i64) -> Vec<String> {
    let mut lines: Vec<String> = vec![];
    
    // Declare initial variables.
    let mut i: i64 = 0;
    while i < var_count {
        lines.push(format!("{}{}", format!("{}{}", format!("{}{}", ("let v").to_string(), (i).to_string()), (" = ").to_string()), (i + 1).to_string()));
        i += 1;
    }
    // Force evaluation of many arithmetic expressions.
    let mut i: i64 = 0;
    while i < loops {
        let x: i64 = i % var_count;
        let y: i64 = (i + 3) % var_count;
        let c1: i64 = i % 7 + 1;
        let c2: i64 = i % 11 + 2;
        lines.push(format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", format!("{}{}", ("v").to_string(), (x).to_string()), (" = (v").to_string()), (x).to_string()), (" * ").to_string()), (c1).to_string()), (" + v").to_string()), (y).to_string()), (" + 10000) / ").to_string()), (c2).to_string()));
        if i % 97 == 0 {
            lines.push(format!("{}{}", ("print v").to_string(), (x).to_string()));
        }
        i += 1;
    }
    // Print final values together.
    lines.push(("print (v0 + v1 + v2 + v3)").to_string());
    return lines;
}

fn run_demo() {
    let mut demo_lines: Vec<String> = vec![];
    demo_lines.push(("let a = 10").to_string());
    demo_lines.push(("let b = 3").to_string());
    demo_lines.push(("a = (a + b) * 2").to_string());
    demo_lines.push(("print a").to_string());
    demo_lines.push(("print a / b").to_string());
    
    let tokens: Vec<Token> = tokenize(&(demo_lines));
    let mut parser: Parser = Parser::new((tokens).clone());
    let stmts: Vec<StmtNode> = parser.parse_program();
    let checksum: i64 = execute(&(stmts), &(parser.expr_nodes), true);
    println!("{} {}", ("demo_checksum:").to_string(), checksum);
}

fn run_benchmark() {
    let source_lines: Vec<String> = build_benchmark_source(32, 120000);
    let start: f64 = perf_counter();
    let tokens: Vec<Token> = tokenize(&(source_lines));
    let mut parser: Parser = Parser::new((tokens).clone());
    let stmts: Vec<StmtNode> = parser.parse_program();
    let checksum: i64 = execute(&(stmts), &(parser.expr_nodes), false);
    let elapsed: f64 = perf_counter() - start;
    
    println!("{} {}", ("token_count:").to_string(), tokens.len() as i64);
    println!("{} {}", ("expr_count:").to_string(), parser.expr_nodes.len() as i64);
    println!("{} {}", ("stmt_count:").to_string(), stmts.len() as i64);
    println!("{} {}", ("checksum:").to_string(), checksum);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn __pytra_main() {
    run_demo();
    run_benchmark();
}

fn main() {
    __pytra_main();
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
