import React from 'react';
import { ArrowUpRight } from 'lucide-react';
import { fmt } from '../../../lib/format';
export function ForecastQuality({ metrics, onMethodology }) {
  return (
    <div className="card insight">
      <div className="eyebrow">FORECAST QUALITY</div>
      <h2>Know the size of the miss.</h2>
      <p>
        Evaluate the forecast available at your decision time, with transparent
        coverage.
      </p>
      <div className="quality">
        <div>
          <small>RMSE</small>
          <strong>
            {fmt(metrics.rmse)} <em>MW</em>
          </strong>
        </div>
        <div>
          <small>WAPE</small>
          <strong>
            {fmt(metrics.wape, 1)} <em>%</em>
          </strong>
        </div>
      </div>
      <button className="text-button" onClick={onMethodology}>
        Explore the methodology <ArrowUpRight size={16} />
      </button>
    </div>
  );
}
