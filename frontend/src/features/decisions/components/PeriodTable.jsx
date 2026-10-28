import React from 'react';
import { Download } from 'lucide-react';
import { fmt } from '../../../lib/format';
import { getDecisionExportURL } from '../api/decisions';
export function PeriodTable({ rows, day, cutoff }) {
  return (
    <div className="card table-card">
      <div className="table-head">
        <h2>Half-hourly detail</h2>
        <a className="export" href={getDecisionExportURL(day, cutoff)}>
          <Download size={14} /> Export CSV
        </a>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Delivery time</th>
              <th>Forecast MW</th>
              <th>Actual MW</th>
              <th>Error MW</th>
              <th>Published</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.start_time}>
                <td>{r.start_time.slice(11, 16)}</td>
                <td>{fmt(r.forecast)}</td>
                <td>{fmt(r.actual)}</td>
                <td className={r.error > 0 ? 'positive' : ''}>
                  {r.error > 0 ? '+' : ''}
                  {fmt(r.error)}
                </td>
                <td>
                  {r.publish_time
                    ? new Date(r.publish_time).toLocaleString('en-GB', {
                        timeZone: 'Europe/London',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
