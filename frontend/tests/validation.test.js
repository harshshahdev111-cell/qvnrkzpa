import assert from 'node:assert/strict';
import test from 'node:test';
import {
  validateDecisionInput,
  assertDecisionInput,
} from '../src/features/decisions/validation/input.js';
import {
  validateDashboard,
  validateSourceStatus,
} from '../src/features/decisions/validation/responses.js';
import { getJSON } from '../src/lib/api.js';

const dashboard = () => ({
  decision_time: '2026-01-15T10:00:00Z',
  delivery_date: '2026-01-16',
  rows: Array.from({ length: 48 }, (_, index) => ({
    start_time: new Date(Date.UTC(2026, 0, 16, 0, index * 30)).toISOString(),
    forecast: null,
    actual: 0,
    error: null,
    publish_time: null,
  })),
  metrics: {
    mae: null,
    rmse: null,
    bias: null,
    wape: null,
    forecast_energy_mwh: null,
    matched_periods: 0,
    forecast_periods: 0,
    actual_periods: 48,
    expected_periods: 48,
  },
});

test('valid January boundaries and cutoff times are accepted', () => {
  for (const day of ['2026-01-01', '2026-01-31'])
    for (const cutoff of ['00:00', '23:59'])
      assert.deepEqual(validateDecisionInput(day, cutoff), {});
});
test('missing, out-of-range and malformed input is rejected', () => {
  for (const day of ['', null, '2026-02-01', '2026-01-32', '2026-1-15'])
    assert.ok(validateDecisionInput(day, '10:00').day);
  for (const cutoff of [
    '',
    null,
    '24:00',
    '10:60',
    '9:00',
    '10:00Z',
    '<script>',
  ])
    assert.throws(() => assertDecisionInput('2026-01-15', cutoff));
});
test('zero actuals and null forecasts are valid', () =>
  assert.deepEqual(validateDashboard(dashboard()), dashboard()));
test('bad series and non-finite metrics are rejected', () => {
  for (const change of [
    (data) => (data.rows = 'bad'),
    (data) => data.rows.pop(),
    (data) => (data.metrics.mae = Infinity),
    (data) => (data.rows[1].start_time = data.rows[0].start_time),
    (data) => (data.rows[0].actual = '100'),
  ]) {
    const data = dashboard();
    change(data);
    assert.throws(() => validateDashboard(data), /invalid data/);
  }
});
test('invalid source status is rejected', () => {
  assert.throws(() => validateSourceStatus({ actuals: -1 }), /invalid data/);
  assert.ok(
    validateSourceStatus({
      source: 'Elexon',
      actuals: 0,
      forecasts: 0,
      synthetic: false,
      last_import: null,
    }),
  );
});
test('API client rejects malformed envelopes and non-JSON', async (t) => {
  for (const payload of [
    null,
    [],
    { success: true },
    { success: true, status_code: 500, message: 'OK', data: {}, errors: null },
  ]) {
    t.mock.method(globalThis, 'fetch', async () => ({
      ok: true,
      status: 200,
      json: async () => payload,
    }));
    await assert.rejects(getJSON('status/'), /invalid response/);
    t.mock.restoreAll();
  }
  t.mock.method(globalThis, 'fetch', async () => ({
    ok: true,
    status: 200,
    json: async () => {
      throw new SyntaxError();
    },
  }));
  await assert.rejects(getJSON('status/'), /invalid JSON/);
});
