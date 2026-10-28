export const API = (import.meta.env?.VITE_API_URL || '').replace(/\/$/, '');

export async function getJSON(path, signal) {
  const response = await fetch(`${API}/api/v1/${path}`, { signal });
  let payload;
  try {
    payload = await response.json();
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new Error('The service returned invalid JSON. Please retry.');
  }
  if (
    !payload ||
    typeof payload !== 'object' ||
    Array.isArray(payload) ||
    typeof payload.success !== 'boolean' ||
    typeof payload.message !== 'string' ||
    payload.status_code !== response.status ||
    !Object.hasOwn(payload, 'data') ||
    !Object.hasOwn(payload, 'errors') ||
    payload.success !== response.ok ||
    (payload.success && payload.errors !== null) ||
    (!payload.success && payload.data !== null)
  ) {
    throw new Error('The service returned an invalid response. Please retry.');
  }
  if (!response.ok || !payload.success) {
    const error = new Error(
      payload.message ||
        'The service could not load this decision. Please retry.',
    );
    error.status = response.status;
    error.errors = payload.errors;
    throw error;
  }
  return payload.data;
}
