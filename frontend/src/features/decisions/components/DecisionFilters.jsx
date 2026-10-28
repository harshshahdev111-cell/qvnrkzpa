import React from 'react';
import { CalendarDays } from 'lucide-react';
import { DECISION_RANGE } from '../constants';
export function DecisionFilters({
  errors = {},
  day,
  cutoff,
  deliveryDate,
  onDayChange,
  onCutoffChange,
}) {
  return (
    <div className="filters card">
      <div className="filter-title">
        <CalendarDays size={19} />
        <div>
          <strong>Build your decision view</strong>
          <small>Forecasts available at the time you buy</small>
        </div>
      </div>
      <label>
        Decision date
        <input
          aria-label="Decision date"
          required
          aria-invalid={Boolean(errors.day)}
          aria-describedby={errors.day ? 'decision-date-error' : undefined}
          type="date"
          min={DECISION_RANGE.start}
          max={DECISION_RANGE.end}
          value={day}
          onChange={(e) => {
            onDayChange(e.target.value);
          }}
        />
        {errors.day && (
          <span id="decision-date-error" className="field-error">
            {errors.day}
          </span>
        )}
      </label>
      <label>
        Cutoff · London time
        <input
          aria-label="Decision cutoff"
          required
          aria-invalid={Boolean(errors.cutoff)}
          aria-describedby={errors.cutoff ? 'decision-cutoff-error' : undefined}
          type="time"
          value={cutoff}
          onChange={(e) => {
            onCutoffChange(e.target.value);
          }}
        />
        {errors.cutoff && (
          <span id="decision-cutoff-error" className="field-error">
            {errors.cutoff}
          </span>
        )}
      </label>
      <div className="delivery">
        DELIVERY DAY<strong>{deliveryDate || '—'}</strong>
      </div>
    </div>
  );
}
