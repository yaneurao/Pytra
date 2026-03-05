using System;

namespace Pytra.CsModule
{
    // Python の math モジュール相当（sample 実行で使う最小集合）。
    public static class math
    {
        public const double pi = Math.PI;
        public const double e = Math.E;
        public const double tau = Math.PI * 2.0;

        public static double sin(double x) { return Math.Sin(x); }
        public static double cos(double x) { return Math.Cos(x); }
        public static double tan(double x) { return Math.Tan(x); }
        public static double asin(double x) { return Math.Asin(x); }
        public static double acos(double x) { return Math.Acos(x); }
        public static double atan(double x) { return Math.Atan(x); }
        public static double atan2(double y, double x) { return Math.Atan2(y, x); }
        public static double sqrt(double x) { return Math.Sqrt(x); }
        public static double exp(double x) { return Math.Exp(x); }
        public static double log(double x) { return Math.Log(x); }
        public static double floor(double x) { return Math.Floor(x); }
        public static double ceil(double x) { return Math.Ceiling(x); }
        public static double fabs(double x) { return Math.Abs(x); }
        public static double pow(double x, double y) { return Math.Pow(x, y); }
    }
}
