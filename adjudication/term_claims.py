"""Exact local term edges and bounded, source-bound interpretation claims.

The tokenizer and grammar remain authoritative. A boundary contributes only a
single occurrence-specific Term edge; it never changes the global lexicon.
"""
from copy import deepcopy
import hashlib
import json

from analysis_parser import construction_ir, inputs

from .anchors import validate_anchor


ANCHOR_FIELDS = ('doc_id', 'reading_id', 'source_sha256', 'start', 'end', 'quote')


def _canonical_anchor(anchor):
    return {key: anchor[key] for key in ANCHOR_FIELDS}


def _document_anchor(doc, anchor):
    from domain_kernel.engine import term_tokens as _kernel_term_tokens
    _kernel_term_tokens(doc, [_canonical_anchor(anchor)])


def validate_term_boundary(packet, anchor, branch_id='main'):
    """Return a durable exact occurrence, including the owning branch."""
    if not isinstance(branch_id, str) or not branch_id:
        raise ValueError('term_branch_required')
    validated = validate_anchor(packet, anchor)
    doc = next(doc for doc in inputs.documents(packet) if doc['doc_id'] == validated['doc_id'])
    _document_anchor(doc, validated)
    return {'anchor': _canonical_anchor(validated), 'branch_id': branch_id}


def _claim_anchor(claim):
    return claim.get('target', claim.get('anchor', claim)) if isinstance(claim, dict) else claim


def term_tokens(doc, boundary_claims):
    from domain_kernel.engine import term_tokens as _kernel_term_tokens
    return _kernel_term_tokens(doc, [_canonical_anchor(_claim_anchor(row)) for row in boundary_claims])


def parse_with_term_boundaries(doc, boundary_claims):
    """Run the ordinary grammar over tokens with reviewed local edges."""
    return construction_ir.parse_syntax(term_tokens(doc, boundary_claims), doc)


def prepare_term_parser(parser, boundary_claims):
    """Refresh affected parser streams before the existing Program IR rebuild.

    The caller must include these document IDs in `_rebuild_program`'s
    changed_documents so its syntax view is rebuilt from the revised stream.
    """
    grouped = {}
    for claim in boundary_claims:
        anchor = _claim_anchor(claim)
        grouped.setdefault(anchor['doc_id'], []).append(claim)
    docs = {doc['doc_id']: doc for doc in parser.docs}
    unknown = set(grouped) - set(docs)
    if unknown:
        raise ValueError('term_boundary_unknown_document')
    for doc_id, claims in grouped.items():
        doc = docs[doc_id]
        syntax = parse_with_term_boundaries(doc, claims)
        parser.all_candidates[doc_id] = syntax.candidates()
        parser.program.syntax_results[doc_id] = syntax
        parser.report['tokens'] = [token for token in parser.report['tokens']
                                   if token['source_span']['doc_id'] != doc_id] + term_tokens(doc, claims)
    return set(grouped)


def apply_term_interpretations(parser, claims):
    """Attach meaning constraints to exact nominal slots, without numeric facts.

    Claims are already replay-reduced and revalidated by the caller. Rejections
    remain negative evidence and never erase construction grammar candidates.
    """
    by_doc = {doc['doc_id']: [] for doc in parser.docs}
    for row in claims:
        claim = row.get('claim', row)
        anchor = claim['anchor']
        if anchor['doc_id'] not in by_doc:
            raise ValueError('term_interpretation_unknown_document')
        by_doc[anchor['doc_id']].append((row.get('decision_id'), claim))
    for doc_id, pairs in by_doc.items():
        if not pairs:
            continue
        syntax = parser.program.syntax_results[doc_id]
        nodes = {node['id']: node for node in syntax.nodes}
        for candidate in parser.all_candidates[doc_id]:
            parent = nodes.get(candidate['node_id'])
            if parent is None:
                continue
            for slot_name, node_id in parent['slots'].items():
                leaf = nodes[node_id]
                if leaf['kind'] != 'Term':
                    continue
                for decision_id, claim in pairs:
                    anchor = claim['anchor']
                    if not any(_same_occurrence(span, anchor) for span in leaf['source_spans']):
                        continue
                    evidence = {'slot': slot_name, 'anchor': deepcopy(anchor),
                                'decision_id': decision_id, 'origin': claim['origin']}
                    if claim['origin'] == 'machine_rejection':
                        evidence['candidate_ids'] = list(claim['candidate_ids'])
                        candidate.setdefault('attributes', {}).setdefault('rejected_term_interpretations', []).append(evidence)
                    else:
                        evidence['expression'] = deepcopy(claim['expression'])
                        if claim['origin'] == 'machine_adoption':
                            evidence['candidate_snapshot'] = deepcopy(claim['candidate_snapshot'])
                        candidate.setdefault('attributes', {}).setdefault('reviewed_term_interpretations', []).append(evidence)
    return parser


def _same_occurrence(left, right):
    return all(left.get(key) == right.get(key) for key in ('doc_id', 'reading_id', 'start', 'end', 'quote')) and (
        'source_sha256' not in left or left['source_sha256'] == right.get('source_sha256'))


def _bundle_candidate(anchor, candidate_id, bundle):
    if bundle['identity']['doc_id'] != anchor['doc_id'] or bundle['identity']['reading_id'] != anchor['reading_id'] \
            or bundle['identity']['source_sha256'] != anchor['source_sha256']:
        raise ValueError('term_candidate_bundle_source')
    candidates = [row for row in bundle['candidates'] if row['id'] == candidate_id
                  and _same_occurrence(row['span'], anchor)]
    if len(candidates) != 1 or candidates[0]['constraint_status'] != 'compatible':
        raise ValueError('term_candidate_not_current_or_compatible')
    return candidates[0]


def _snapshot(candidate, bundle):
    return {'candidate_id': candidate['id'], 'bundle_identity': deepcopy(bundle['identity']),
            'expression': deepcopy(candidate['expression']), 'cue_id': candidate['cue_id'],
            'rule_id': candidate['rule_id'], 'provenance_ids': list(candidate['provenance_ids']),
            'truncated': bundle['truncated'], 'source_anchor': deepcopy(candidate['span'])}


def adopt_term_candidate(anchor, branch_id, candidate, bundle):
    """Make a proposal a reviewed expression with its full snapshot evidence."""
    candidate_id = candidate['id'] if isinstance(candidate, dict) else candidate
    current = _bundle_candidate(anchor, candidate_id, bundle)
    if isinstance(candidate, dict) and candidate != current:
        raise ValueError('term_candidate_snapshot_mismatch')
    if not branch_id:
        raise ValueError('term_branch_required')
    snapshot = _snapshot(current, bundle)
    return {'schema': 'TermInterpretationClaim/1', 'origin': 'machine_adoption',
            'anchor': _canonical_anchor(anchor), 'branch_id': branch_id,
            'expression': deepcopy(current['expression']), 'candidate_snapshot': snapshot}


def reject_term_candidates(anchor, branch_id, candidate_ids, bundle):
    if not branch_id or not isinstance(candidate_ids, list) or not candidate_ids or len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError('term_rejection_requires_distinct_candidates')
    snapshots = [_snapshot(_bundle_candidate(anchor, candidate_id, bundle), bundle)
                 for candidate_id in candidate_ids]
    return {'schema': 'TermInterpretationClaim/1', 'origin': 'machine_rejection',
            'anchor': _canonical_anchor(anchor), 'branch_id': branch_id,
            'candidate_ids': list(candidate_ids), 'candidate_snapshots': snapshots}


def _validate_composition(expression, registry, quote):
    from domain_kernel.engine import _sort
    concepts = {row['id']: row for row in registry['concepts']}
    constructors = {row['id']: row for row in registry['constructors']}
    _sort(expression, concepts, constructors)
    allowed_ops = {row['build']['op'] for row in registry['composition_rules']}
    def visit(node):
        if node['op'] == 'concept':
            if not any(cue['form'] in quote and node['concept_id'] in cue['sense_concept_ids']
                       for cue in registry['lexical_cues']):
                raise ValueError('term_composition_not_source_applicable')
        elif node['op'] not in allowed_ops:
            raise ValueError('term_composition_rule_not_registered')
        else:
            for child in node['arguments'].values():
                visit(child)
    visit(expression)


def compose_term_interpretation(anchor, branch_id, expression, *, registry=None):
    """Validate a human expression against current registry and local source."""
    from domain_kernel.engine import load_kernel
    if not branch_id:
        raise ValueError('term_branch_required')
    kernel = load_kernel() if registry is None else registry
    _validate_composition(expression, kernel, anchor['quote'])
    return {'schema': 'TermInterpretationClaim/1', 'origin': 'human_composition',
            'anchor': _canonical_anchor(anchor), 'branch_id': branch_id,
            'expression': deepcopy(expression),
            'registry_sha256': hashlib.sha256(json.dumps(kernel, ensure_ascii=False, sort_keys=True,
                                                        separators=(',', ':')).encode('utf-8')).hexdigest()}


def revalidate_term_interpretation(claim, packet, *, term_boundaries=(), registry=None, branch_id=None):
    """Rebuild K from source + boundaries; the claim is never a generator input."""
    from domain_kernel.engine import suggest_term_semantics
    try:
        anchor = validate_anchor(packet, claim['anchor'])
        if branch_id is not None and claim['branch_id'] != branch_id:
            raise ValueError('term_branch_mismatch')
        doc = next(doc for doc in inputs.documents(packet) if doc['doc_id'] == anchor['doc_id'])
        boundaries = [_claim_anchor(row) for row in term_boundaries if _claim_anchor(row)['doc_id'] == doc['doc_id']]
        bundle = suggest_term_semantics(doc, registry=registry, term_boundaries=boundaries)
        if claim['origin'] == 'human_composition':
            from domain_kernel.engine import load_kernel
            kernel = load_kernel() if registry is None else registry
            _validate_composition(claim['expression'], kernel, anchor['quote'])
            return {'status': 'valid', 'origin': 'human_composition', 'bundle_identity': bundle['identity']}
        if claim['origin'] == 'machine_adoption' and claim.get('expression') != claim['candidate_snapshot']['expression']:
            raise ValueError('term_claim_expression_snapshot_mismatch')
        snapshots = ([claim['candidate_snapshot']] if claim['origin'] == 'machine_adoption'
                     else claim['candidate_snapshots'] if claim['origin'] == 'machine_rejection' else [])
        if not snapshots:
            raise ValueError('term_claim_origin')
        for snapshot in snapshots:
            candidate = _bundle_candidate(anchor, snapshot['candidate_id'], bundle)
            if _snapshot(candidate, bundle) != snapshot:
                raise ValueError('term_candidate_context_changed')
        return {'status': 'valid', 'origin': claim['origin'], 'bundle_identity': bundle['identity']}
    except (ValueError, KeyError, TypeError) as error:
        return {'status': 'needs_revalidation', 'reason': str(error)}
