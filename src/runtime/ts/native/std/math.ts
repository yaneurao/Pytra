// Python の math モジュール互換（最小実装）。

export const pi: number = Math.PI;
export const e: number = Math.E;

export function sin(v: number): number { return Math.sin(v); }
export function cos(v: number): number { return Math.cos(v); }
export function tan(v: number): number { return Math.tan(v); }
export function sqrt(v: number): number { return Math.sqrt(v); }
export function exp(v: number): number { return Math.exp(v); }
export function log(v: number): number { return Math.log(v); }
export function log10(v: number): number { return Math.log10(v); }
export function fabs(v: number): number { return Math.abs(v); }
export function floor(v: number): number { return Math.floor(v); }
export function ceil(v: number): number { return Math.ceil(v); }
export function pow(a: number, b: number): number { return Math.pow(a, b); }
