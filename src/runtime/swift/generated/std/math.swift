// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/math.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func sqrt(_ x: Double) -> Double {
    return pyMathSqrt(__pytra_float(x))
}

func sin(_ x: Double) -> Double {
    return pyMathSin(__pytra_float(x))
}

func cos(_ x: Double) -> Double {
    return pyMathCos(__pytra_float(x))
}

func tan(_ x: Double) -> Double {
    return pyMathTan(__pytra_float(x))
}

func exp(_ x: Double) -> Double {
    return pyMathExp(__pytra_float(x))
}

func log(_ x: Double) -> Double {
    return pyMathLog(__pytra_float(x))
}

func log10(_ x: Double) -> Double {
    return pyMathLog10(__pytra_float(x))
}

func fabs(_ x: Double) -> Double {
    return pyMathFabs(__pytra_float(x))
}

func floor(_ x: Double) -> Double {
    return pyMathFloor(__pytra_float(x))
}

func ceil(_ x: Double) -> Double {
    return pyMathCeil(__pytra_float(x))
}

func pow(_ x: Double, _ y: Double) -> Double {
    return pyMathPow(__pytra_float(x), __pytra_float(y))
}
