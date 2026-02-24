// Python の time モジュール互換（最小実装）。

/** Python の perf_counter 相当。 */
function perfCounter() {
  return Number(process.hrtime.bigint()) / 1_000_000_000;
}

module.exports = { perfCounter };
