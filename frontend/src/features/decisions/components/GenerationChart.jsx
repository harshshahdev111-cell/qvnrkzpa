import React from 'react';
import { Info } from 'lucide-react';
import { fmt } from '../../../lib/format';
import { buildSeriesPath, getChartMaximum } from '../utils/chart';
export function GenerationChart({ rows, day, cutoff }) {
  const maximum = getChartMaximum(rows);
  return (
    <div className="chart card">
      <div className="chart-heading">
        <div>
          <h2>Tomorrow’s wind, in perspective</h2>
          <p>Latest eligible forecast against delivered generation · MW</p>
        </div>
        <div className="legend">
          <span>
            <i /> Forecast
          </span>
          <span>
            <i className="actual" /> Actual
          </span>
        </div>
      </div>
      <svg
        viewBox="0 0 980 290"
        role="img"
        aria-label="Half-hourly wind forecast and actual generation chart"
      >
        {[0, 1, 2, 3, 4].map((i) => (
          <g key={i}>
            <line
              x1="60"
              x2="940"
              y1={245 - i * 51.25}
              y2={245 - i * 51.25}
              stroke="#e9eeed"
            />
            <text x="46" y={249 - i * 51.25} textAnchor="end">
              {fmt((maximum * i) / 4)}
            </text>
          </g>
        ))}
        {[0, 8, 16, 24, 32, 40, 47].map((i) => (
          <text
            key={i}
            x={60 + (i * 880) / 47}
            y="275"
            textAnchor="middle"
          >{`${String(Math.floor(i / 2)).padStart(2, '0')}:${i % 2 ? '30' : '00'}`}</text>
        ))}
        {rows.map((r, i) =>
          r.forecast == null ? null : (
            <circle
              key={r.start_time}
              cx={60 + (i * 880) / 47}
              cy={245 - (r.forecast / maximum) * 205}
              r="3"
              fill="#078c73"
            />
          ),
        )}
        <path
          d={buildSeriesPath(rows, 'forecast', maximum)}
          stroke="#078c73"
          strokeWidth="3"
          fill="none"
        />
        <path
          d={buildSeriesPath(rows, 'actual', maximum)}
          stroke="#84949f"
          strokeWidth="2.5"
          strokeDasharray="6 4"
          fill="none"
        />
        {rows.filter((r) => r.forecast != null || r.actual != null).length ===
          0 && (
          <text x="500" y="140" textAnchor="middle">
            No data for this decision cutoff
          </text>
        )}
      </svg>
      <div className="chart-foot">
        <span>
          <Info size={14} /> Forecast vintages published after {cutoff} on {day}{' '}
          are excluded.
        </span>
        <span>30-minute resolution</span>
      </div>
    </div>
  );
}
