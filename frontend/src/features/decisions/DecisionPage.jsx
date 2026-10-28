import React, { useState } from 'react';
import { DEFAULT_CUTOFF, DEFAULT_DECISION_DATE } from './constants';
import { useDecision } from './hooks/useDecision';
import { DecisionHeading } from './components/DecisionHeading';
import { DecisionFilters } from './components/DecisionFilters';
import { MetricCards } from './components/MetricCards';
import { GenerationChart } from './components/GenerationChart';
import { ForecastQuality } from './components/ForecastQuality';
import { PeriodTable } from './components/PeriodTable';
import { SourceFooter } from './components/SourceFooter';
import { Methodology } from './components/Methodology';

export function DecisionPage({ activePage, onMethodology }) {
  const [day, setDay] = useState(DEFAULT_DECISION_DATE);
  const [cutoff, setCutoff] = useState(DEFAULT_CUTOFF);
  const { data, status, error, busy, retry, fieldErrors } = useDecision(
    day,
    cutoff,
  );
  const metrics = data?.metrics ?? {};
  const rows = data?.rows ?? [];

  return (
    <>
      <DecisionHeading activePage={activePage} />
      {activePage === 'method' ? (
        <Methodology />
      ) : (
        <>
          <DecisionFilters
            errors={fieldErrors}
            day={day}
            cutoff={cutoff}
            deliveryDate={
              busy || error || Object.keys(fieldErrors).length
                ? null
                : data?.delivery_date
            }
            onDayChange={setDay}
            onCutoffChange={setCutoff}
          />
          {Object.keys(fieldErrors).length ? (
            <div className="notice" role="alert">
              Correct the highlighted fields to load the decision view.
            </div>
          ) : error ? (
            <div role="alert" className="notice">
              {error} <button onClick={retry}>Retry</button>
            </div>
          ) : busy ? (
            <div className="notice" role="status">
              Loading decision data…
            </div>
          ) : (
            <>
              {!metrics.forecast_periods && (
                <div className="notice">
                  No forecasts available for this cutoff. Import Elexon data or
                  select another decision time.
                </div>
              )}
              <MetricCards metrics={metrics} />
              <GenerationChart rows={rows} day={day} cutoff={cutoff} />
              <div className="lower">
                <ForecastQuality
                  metrics={metrics}
                  onMethodology={onMethodology}
                />
                <PeriodTable rows={rows} day={day} cutoff={cutoff} />
              </div>
            </>
          )}
          <SourceFooter status={status} />
        </>
      )}
    </>
  );
}
