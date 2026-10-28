export const fmt = (value, digits = 0) =>
  value == null
    ? '—'
    : Number(value).toLocaleString('en-GB', { maximumFractionDigits: digits });
