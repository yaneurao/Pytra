// Python の time モジュール互換（最小実装）。

/** Python の perf_counter 相当。 */
export function perfCounter(): number {
  return Number(process.hrtime.bigint()) / 1_000_000_000;
}
