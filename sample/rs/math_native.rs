pub const pi: f64 = ::std::f64::consts::PI;
pub const e: f64 = ::std::f64::consts::E;

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

pub fn cos<T: ToF64>(v: T) -> f64 {
    v.to_f64().cos()
}

pub fn tan<T: ToF64>(v: T) -> f64 {
    v.to_f64().tan()
}

pub fn sqrt<T: ToF64>(v: T) -> f64 {
    v.to_f64().sqrt()
}

pub fn exp<T: ToF64>(v: T) -> f64 {
    v.to_f64().exp()
}

pub fn log<T: ToF64>(v: T) -> f64 {
    v.to_f64().ln()
}

pub fn log10<T: ToF64>(v: T) -> f64 {
    v.to_f64().log10()
}

pub fn fabs<T: ToF64>(v: T) -> f64 {
    v.to_f64().abs()
}

pub fn floor<T: ToF64>(v: T) -> f64 {
    v.to_f64().floor()
}

pub fn ceil<T: ToF64>(v: T) -> f64 {
    v.to_f64().ceil()
}

pub fn pow(a: f64, b: f64) -> f64 {
    a.powf(b)
}
