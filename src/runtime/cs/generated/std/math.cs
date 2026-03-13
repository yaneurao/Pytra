// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/math.py
// generated-by: tools/gen_runtime_from_manifest.py

using System;
using System.Collections.Generic;
using System.Linq;
using Any = System.Object;
using int64 = System.Int64;
using float64 = System.Double;
using str = System.String;

namespace Pytra.CsModule
{
    public static class math
    {
        public static double pi { get { return math_native.pi; } }
        public static double e { get { return math_native.e; } }

        public static float64 sqrt(float64 x)
        {
            return math_native.sqrt(x);
        }

        public static float64 sin(float64 x)
        {
            return math_native.sin(x);
        }

        public static float64 cos(float64 x)
        {
            return math_native.cos(x);
        }

        public static float64 tan(float64 x)
        {
            return math_native.tan(x);
        }

        public static float64 exp(float64 x)
        {
            return math_native.exp(x);
        }

        public static float64 log(float64 x)
        {
            return math_native.log(x);
        }

        public static float64 log10(float64 x)
        {
            return math_native.log10(x);
        }

        public static float64 fabs(float64 x)
        {
            return math_native.fabs(x);
        }

        public static float64 floor(float64 x)
        {
            return math_native.floor(x);
        }

        public static float64 ceil(float64 x)
        {
            return math_native.ceil(x);
        }

        public static float64 pow(float64 x, float64 y)
        {
            return math_native.pow(x, y);
        }

    }
}
