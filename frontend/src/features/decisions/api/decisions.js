import { API, getJSON } from '../../../lib/api';
import { assertDecisionInput } from '../validation/input';
import {
  validateDashboard,
  validateSourceStatus,
} from '../validation/responses';

export function getDecision(day, cutoff, signal) {
  assertDecisionInput(day, cutoff);
  const query = new URLSearchParams({ decision_date: day, cutoff });
  return getJSON(`dashboard/?${query}`, signal).then(validateDashboard);
}

export function getSourceStatus(signal) {
  return getJSON('status/', signal).then(validateSourceStatus);
}

export function getDecisionExportURL(day, cutoff) {
  assertDecisionInput(day, cutoff);
  const query = new URLSearchParams({
    decision_date: day,
    cutoff,
    export: 'csv',
  });
  return `${API}/api/v1/dashboard/?${query}`;
}
