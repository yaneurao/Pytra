using System;

namespace Pytra.CsModule
{
    // Generated std/math.cs delegates host bindings through this native seam.
    public static class math_native
    {
        public static double pi { get { return Math.PI; } }
        public static double e { get { return Math.E; } }

        public static double sqrt(double x)
        {
            return Math.Sqrt(x);
        }

        public static double sin(double x)
        {
            return Math.Sin(x);
        }

        public static double cos(double x)
        {
            return Math.Cos(x);
        }

        public static double tan(double x)
        {
            return Math.Tan(x);
        }

        public static double exp(double x)
        {
            return Math.Exp(x);
        }

        public static double log(double x)
        {
            return Math.Log(x);
        }

        public static double log10(double x)
        {
            return Math.Log10(x);
        }

        public static double fabs(double x)
        {
            return Math.Abs(x);
        }

        public static double floor(double x)
        {
            return Math.Floor(x);
        }

        public static double ceil(double x)
        {
            return Math.Ceiling(x);
        }

        public static double pow(double x, double y)
        {
            return Math.Pow(x, y);
        }
    }
}
