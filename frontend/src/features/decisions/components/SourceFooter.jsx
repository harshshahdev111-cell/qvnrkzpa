import React from 'react';

export function SourceFooter({ status }) {
  return (
    <footer>
      <span>
        <span className="green-dot" /> Source: Elexon BMRS · FUELHH & WINDFOR
      </span>
      <span>
        Last import:{' '}
        {status?.last_import
          ? new Date(status.last_import).toLocaleString('en-GB', {
              timeZone: 'Europe/London',
            })
          : 'Not yet imported'}{' '}
        · London time
      </span>
    </footer>
  );
}
