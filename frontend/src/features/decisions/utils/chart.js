export function getChartMaximum(rows) {
  return (
    Math.max(
      1000,
      ...rows.flatMap((row) => [row.forecast ?? 0, row.actual ?? 0]),
    ) * 1.15
  );
}

export function buildSeriesPath(rows, key, maximum) {
  let path = '';
  let connected = false;
  rows.forEach((row, index) => {
    if (row[key] == null) {
      connected = false;
      return;
    }
    path += `${connected ? 'L' : 'M'}${60 + (index * 880) / 47},${245 - (row[key] / maximum) * 205} `;
    connected = true;
  });
  return path;
}
