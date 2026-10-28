import { useEffect, useState } from 'react';
import { getDecision, getSourceStatus } from '../api/decisions';
import { validateDecisionInput } from '../validation/input';

export function useDecision(day, cutoff) {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(true);
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    if (Object.keys(validateDecisionInput(day, cutoff)).length) {
      setBusy(false);
      setData(null);
      setError('');
      return;
    }
    const controller = new AbortController();
    setBusy(true);
    setError('');
    Promise.all([
      getDecision(day, cutoff, controller.signal),
      getSourceStatus(controller.signal),
    ])
      .then(([dashboard, source]) => {
        if (controller.signal.aborted) return;
        setData(dashboard);
        setStatus(source);
      })
      .catch((error) => {
        if (!controller.signal.aborted) setError(error.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setBusy(false);
      });
    return () => controller.abort();
  }, [day, cutoff, revision]);

  return {
    fieldErrors: validateDecisionInput(day, cutoff),
    data,
    status,
    error,
    busy,
    retry: () => setRevision((value) => value + 1),
  };
}
