import React from 'react';

export function Methodology() {
  return (
    <article className="method card">
      <h2>Decisions grounded in available information</h2>
      <p>
        For every half-hour of the next delivery day, Wind Desk selects the
        latest WINDFOR record whose publishTime is at or before the selected
        decision cutoff. Later revisions are excluded. All displayed times are
        Europe/London (UTC in January and February).
      </p>
      <h3>Accuracy and coverage</h3>
      <p>
        Error = forecast − actual. Positive bias indicates overforecasting,
        potentially leaving a wind shortfall. MAE is mean absolute error; RMSE
        gives larger errors more weight. WAPE = sum of absolute errors ÷ sum of
        absolute actuals × 100. Metrics include matched periods only;
        zero-denominator WAPE is unavailable.
      </p>
      <h3>Scope and limitations</h3>
      <p>
        Only Elexon FUELHH WIND actuals and WINDFOR forecasts are used. These
        represent Elexon’s reported wind coverage, not all UK renewable
        generation. January 1–31 decision dates correspond to January 2–February
        1 delivery dates. The default 10:00 cutoff is an adjustable assumption,
        not a prescribed auction deadline.
      </p>
      <p>
        Forecast energy is MW × 0.5 hours, summed over available periods. It is
        a partial total if coverage is incomplete. This portal cannot calculate
        a procurement quantity without demand and other generation inputs.
        Accuracy is a retrospective evaluation, not a probabilistic confidence
        interval.
      </p>
      <h3>Source and refresh</h3>
      <p>
        Historical data is imported explicitly using the backend import_elexon
        command. The import is transactional and repeatable; no synthetic data
        is substituted when upstream data is unavailable.
      </p>
      <a
        href="https://bmrs.elexon.co.uk/api-documentation"
        target="_blank"
        rel="noreferrer"
      >
        Elexon API documentation ↗
      </a>
    </article>
  );
}
