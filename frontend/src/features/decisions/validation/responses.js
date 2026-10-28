const object = (value) =>
  value !== null && typeof value === 'object' && !Array.isArray(value);
const finite = (value) => typeof value === 'number' && Number.isFinite(value);
const nullableNumber = (value) => value === null || finite(value);
const timestamp = (value) =>
  typeof value === 'string' &&
  /^\d{4}-\d{2}-\d{2}T/.test(value) &&
  Number.isFinite(Date.parse(value));
const count = (value) => Number.isInteger(value) && value >= 0;

export function rejectMalformedResponse() {
  throw new Error('The service returned invalid data. Please retry.');
}

export function validateDashboard(data) {
  if (
    !object(data) ||
    !timestamp(data.decision_time) ||
    typeof data.delivery_date !== 'string' ||
    !/^\d{4}-\d{2}-\d{2}$/.test(data.delivery_date) ||
    !Number.isFinite(Date.parse(data.delivery_date)) ||
    !Array.isArray(data.rows) ||
    data.rows.length !== 48 ||
    !object(data.metrics)
  )
    rejectMalformedResponse();
  const metrics = data.metrics;
  for (const key of ['mae', 'rmse', 'bias', 'wape', 'forecast_energy_mwh']) {
    if (
      !nullableNumber(metrics[key]) ||
      (key !== 'bias' && metrics[key] !== null && metrics[key] < 0)
    )
      rejectMalformedResponse();
  }
  for (const key of [
    'matched_periods',
    'forecast_periods',
    'actual_periods',
    'expected_periods',
  ]) {
    if (!count(metrics[key]) || metrics[key] > 48) rejectMalformedResponse();
  }
  if (
    metrics.expected_periods !== 48 ||
    metrics.matched_periods >
      Math.min(metrics.forecast_periods, metrics.actual_periods)
  )
    rejectMalformedResponse();
  const targets = new Set();
  for (const row of data.rows) {
    if (
      !object(row) ||
      !timestamp(row.start_time) ||
      targets.has(row.start_time) ||
      !nullableNumber(row.forecast) ||
      !nullableNumber(row.actual) ||
      !nullableNumber(row.error) ||
      (row.publish_time !== null && !timestamp(row.publish_time))
    )
      rejectMalformedResponse();
    targets.add(row.start_time);
  }
  return data;
}

export function validateSourceStatus(data) {
  if (
    !object(data) ||
    typeof data.source !== 'string' ||
    !count(data.actuals) ||
    !count(data.forecasts) ||
    typeof data.synthetic !== 'boolean' ||
    (data.last_import !== null && !timestamp(data.last_import))
  )
    rejectMalformedResponse();
  return data;
}
