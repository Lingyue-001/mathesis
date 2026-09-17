// Versioned browser persistence for AdjudicationSession documents only.
// It has no compiler, graph mutation, or page-rendering responsibility.
const PREFIX = 'mathesis.adjudication-session.v1.';

const key = procedureId => `${PREFIX}${procedureId}`;

export function loadSession(procedureId) {
  try {
    const value = JSON.parse(localStorage.getItem(key(procedureId)) || 'null');
    return value?.procedure_id === procedureId && value.session?.schema === 'AdjudicationSession' ? value : null;
  } catch { return null; }
}

export function saveSession(procedureId, session, branchId = 'main') {
  const value = { schema: 'WorkbenchSessionCache', schema_version: '1.0', procedure_id: procedureId, branch_id: branchId, session };
  // One replace operation prevents a partially written decision log from being retained.
  localStorage.setItem(key(procedureId), JSON.stringify(value));
  return value;
}

export function clearSession(procedureId) { localStorage.removeItem(key(procedureId)); }

export function exportSession(procedureId, session, branchId) {
  return JSON.stringify({ schema: 'WorkbenchSessionExport', schema_version: '1.0', procedure_id: procedureId, branch_id: branchId, session }, null, 2);
}

export function importSession(text, procedureId) {
  const value = JSON.parse(text);
  if (value?.schema !== 'WorkbenchSessionExport' || value.procedure_id !== procedureId || value.session?.schema !== 'AdjudicationSession') {
    throw new Error('invalid_session_import');
  }
  return saveSession(procedureId, value.session, value.branch_id || 'main');
}
