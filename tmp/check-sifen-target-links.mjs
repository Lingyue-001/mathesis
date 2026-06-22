import fs from 'node:fs';

const targets = [
  'sifen:L66',
  'sifen:L74',
  'sifen:L84',
  'sifen:L112',
  'sifen:L118',
  'sifen:L122',
  'sifen:L126',
  'sifen:L152',
  'sifen:L154'
];

function collectObjects(x, out = []) {
  if (Array.isArray(x)) {
    for (const item of x) collectObjects(item, out);
    return out;
  }
  if (x && typeof x === 'object') {
    out.push(x);
    for (const value of Object.values(x)) collectObjects(value, out);
  }
  return out;
}

function short(s, n = 180) {
  if (typeof s !== 'string') return '';
  return s.replace(/\s+/g, ' ').slice(0, n);
}

const coverageRaw = JSON.parse(fs.readFileSync('tmp/procedure-ir/cullen-coverage-matrix.json', 'utf8'));
const claimsRaw = JSON.parse(fs.readFileSync('tmp/procedure-ir/cullen-claimbank.json', 'utf8'));

const coverageRows = collectObjects(coverageRaw).filter(o => typeof o.source_span_id === 'string');
const claimRows = collectObjects(claimsRaw).filter(o => typeof o.claim_id === 'string');
const claimById = new Map(claimRows.map(c => [c.claim_id, c]));

for (const id of targets) {
  const row = coverageRows.find(r => r.source_span_id === id);
  console.log('\n=== ' + id + ' ===');
  if (!row) {
    console.log('NO COVERAGE ROW FOUND');
    continue;
  }

  console.log('coverage_status:', row.coverage_status);
  console.log('can_support_A_confirmed:', row.can_support_A_confirmed);
  console.log('blocking_reason:', row.blocking_reason);
  console.log('matched_cullen_claims:', JSON.stringify(row.matched_cullen_claims || []));

  const ids = Array.isArray(row.matched_cullen_claims) ? row.matched_cullen_claims : [];
  for (const cid of ids.slice(0, 5)) {
    const claim = claimById.get(cid);
    if (!claim) {
      console.log('  claim missing in claimbank:', cid);
      continue;
    }
    console.log('  claim:', cid);
    console.log('    system:', claim.system);
    console.log('    type:', claim.claim_type);
    console.log('    evidence_level:', claim.evidence_level);
    console.log('    can_support_A:', claim.can_support_A_confirmed);
    console.log('    chunk:', claim.evidence_chunk_id, 'page:', claim.page_start);
    console.log('    formula:', short(claim.formula_text));
    console.log('    evidence:', short(claim.evidence_text));
  }
}
