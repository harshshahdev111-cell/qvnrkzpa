import React from 'react';
import { CalendarDays } from 'lucide-react';
export function DecisionHeading({ activePage }) {
  return (
    <div className="heading">
      <div>
        <div className="eyebrow">GENERATION INTELLIGENCE</div>
        <h1>
          {activePage === 'method'
            ? 'Behind the numbers'
            : 'A clearer view of tomorrow.'}
        </h1>
        <p>
          Wind generation forecasts and the confidence behind your day-ahead
          decisions.
        </p>
      </div>
      <span className="period">
        <CalendarDays size={16} /> January 2026
      </span>
    </div>
  );
}
