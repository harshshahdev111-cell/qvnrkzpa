import { DECISION_RANGE } from '../constants.js';

export function validateDecisionInput(day, cutoff) {
  const errors = {};
  if (
    typeof day !== 'string' ||
    !/^2026-01-(0[1-9]|[12]\d|3[01])$/.test(day) ||
    day < DECISION_RANGE.start ||
    day > DECISION_RANGE.end
  ) {
    errors.day = 'Choose a date from 1 to 31 January 2026.';
  }
  if (typeof cutoff !== 'string' || !/^([01]\d|2[0-3]):[0-5]\d$/.test(cutoff)) {
    errors.cutoff = 'Enter a valid London time in HH:MM format.';
  }
  return errors;
}

export function assertDecisionInput(day, cutoff) {
  const errors = validateDecisionInput(day, cutoff);
  if (Object.keys(errors).length) {
    const error = new Error('Correct the highlighted decision fields.');
    error.errors = errors;
    throw error;
  }
}
