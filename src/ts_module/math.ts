// Python の math モジュール互換（最小実装）。

export const pi: number = Math.PI;
export const e: number = Math.E;

export function sin(v: number): number { return Math.sin(v); }
export function cos(v: number): number { return Math.cos(v); }
export function sqrt(v: number): number { return Math.sqrt(v); }
export function exp(v: number): number { return Math.exp(v); }
export function floor(v: number): number { return Math.floor(v); }
