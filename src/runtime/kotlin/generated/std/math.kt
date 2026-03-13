// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/math.py
// generated-by: tools/gen_runtime_from_manifest.py



fun sqrt(x: Double): Double {
    return pyMathSqrt(__pytra_float(x))
}

fun sin(x: Double): Double {
    return pyMathSin(__pytra_float(x))
}

fun cos(x: Double): Double {
    return pyMathCos(__pytra_float(x))
}

fun tan(x: Double): Double {
    return pyMathTan(__pytra_float(x))
}

fun exp(x: Double): Double {
    return pyMathExp(__pytra_float(x))
}

fun log(x: Double): Double {
    return pyMathLog(__pytra_float(x))
}

fun log10(x: Double): Double {
    return pyMathLog10(__pytra_float(x))
}

fun fabs(x: Double): Double {
    return pyMathFabs(__pytra_float(x))
}

fun floor(x: Double): Double {
    return pyMathFloor(__pytra_float(x))
}

fun ceil(x: Double): Double {
    return pyMathCeil(__pytra_float(x))
}

fun pow(x: Double, y: Double): Double {
    return pyMathPow(__pytra_float(x), __pytra_float(y))
}
