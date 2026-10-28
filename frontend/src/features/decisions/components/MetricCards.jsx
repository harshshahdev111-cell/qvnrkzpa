import React from 'react';
import { ArrowUpRight, Wind } from 'lucide-react';
import { fmt } from '../../../lib/format';
export function MetricCards({ metrics }) {
  return (
    <div className="metrics">
      {[
        [
          'Forecast energy (available)',
          metrics.forecast_energy_mwh,
          'MWh',
          'Partial total when coverage is below 48',
        ],
        [
          'Mean absolute error',
          metrics.mae,
          'MW',
          'Typical absolute forecast deviation',
        ],
        [
          'Forecast bias',
          metrics.bias,
          'MW',
          'Positive means wind is overforecast',
        ],
        [
          'Matched coverage',
          `${metrics.matched_periods || 0} / 48`,
          'periods',
          'Half-hours used in accuracy metrics',
        ],
      ].map(([title, v, unit, note], i) => (
        <div className="metric card" key={title}>
          <div className="metric-label">
            {title}
            <span>
              {i === 0 ? <Wind size={17} /> : <ArrowUpRight size={16} />}
            </span>
          </div>
          <div className="metric-value">
            {typeof v === 'string' ? v : fmt(v)} <small>{unit}</small>
          </div>
          <p>{note}</p>
        </div>
      ))}
    </div>
  );
}
