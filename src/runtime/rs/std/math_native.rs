pub const pi: f64 = ::std::f64::consts::PI;
pub const math_e: f64 = ::std::f64::consts::E;
pub const py_pi: f64 = pi;
pub const py_e: f64 = math_e;

pub trait ToF64 {
    fn to_f64(self) -> f64;
}

impl ToF64 for f64 {
    fn to_f64(self) -> f64 {
        self
    }
}

impl ToF64 for f32 {
    fn to_f64(self) -> f64 {
        self as f64
    }
}

impl ToF64 for i64 {
    fn to_f64(self) -> f64 {
        self as f64
    }
}

impl ToF64 for i32 {
    fn to_f64(self) -> f64 {
        self as f64
    }
}

impl ToF64 for i16 {
    fn to_f64(self) -> f64 {
        self as f64
    }
}

impl ToF64 for i8 {
    fn to_f64(self) -> f64 {
        self as f64
    }
}

impl ToF64 for u64 {
    fn to_f64(self) -> f64 {
        self as f64
    }
}

impl ToF64 for u32 {
    fn to_f64(self) -> f64 {
        self as f64
    }
}

impl ToF64 for u16 {
    fn to_f64(self) -> f64 {
        self as f64
    }
}

impl ToF64 for u8 {
    fn to_f64(self) -> f64 {
        self as f64
    }
}

impl ToF64 for usize {
    fn to_f64(self) -> f64 {
        self as f64
    }
}

impl ToF64 for isize {
    fn to_f64(self) -> f64 {
        self as f64
    }
}

pub fn sin<T: ToF64>(v: T) -> f64 {
    v.to_f64().sin()
}

pub fn py_sin<T: ToF64>(v: T) -> f64 {
    sin(v)
}

pub fn cos<T: ToF64>(v: T) -> f64 {
    v.to_f64().cos()
}

pub fn py_cos<T: ToF64>(v: T) -> f64 {
    cos(v)
}

pub fn tan<T: ToF64>(v: T) -> f64 {
    v.to_f64().tan()
}

pub fn py_tan<T: ToF64>(v: T) -> f64 {
    tan(v)
}

pub fn sqrt<T: ToF64>(v: T) -> f64 {
    v.to_f64().sqrt()
}

pub fn py_sqrt<T: ToF64>(v: T) -> f64 {
    sqrt(v)
}

pub fn exp<T: ToF64>(v: T) -> f64 {
    v.to_f64().exp()
}

pub fn py_exp<T: ToF64>(v: T) -> f64 {
    exp(v)
}

pub fn log<T: ToF64>(v: T) -> f64 {
    v.to_f64().ln()
}

pub fn py_log<T: ToF64>(v: T) -> f64 {
    log(v)
}

pub fn log10<T: ToF64>(v: T) -> f64 {
    v.to_f64().log10()
}

pub fn py_log10<T: ToF64>(v: T) -> f64 {
    log10(v)
}

pub fn fabs<T: ToF64>(v: T) -> f64 {
    v.to_f64().abs()
}

pub fn py_fabs<T: ToF64>(v: T) -> f64 {
    fabs(v)
}

pub fn floor<T: ToF64>(v: T) -> f64 {
    v.to_f64().floor()
}

pub fn py_floor<T: ToF64>(v: T) -> f64 {
    floor(v)
}

pub fn ceil<T: ToF64>(v: T) -> f64 {
    v.to_f64().ceil()
}

pub fn py_ceil<T: ToF64>(v: T) -> f64 {
    ceil(v)
}

pub fn pow(a: f64, b: f64) -> f64 {
    a.powf(b)
}

pub fn py_pow(a: f64, b: f64) -> f64 {
    pow(a, b)
}
