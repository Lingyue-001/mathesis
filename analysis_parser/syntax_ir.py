"""Token-derived syntax, including alternatives and source coverage."""
from copy import deepcopy
from dataclasses import dataclass,field
@dataclass
class SyntaxResult:
    nodes:list=field(default_factory=list)
    roots:list=field(default_factory=list)
    diagnostics:list=field(default_factory=list)
    token_coverage:list=field(default_factory=list)
    def to_dict(self):
        return {k:getattr(self,k) for k in ('nodes','roots','diagnostics','token_coverage')}
    def candidates(self):
        by_id={n['id']:n for n in self.nodes};out=[]
        def visit(ident):
            n=by_id[ident]
            if n['kind']=='Sequence':
                for child in n['children']:visit(child)
                return
            slots = {}
            for name, child_id in n['slots'].items():
                child = by_id[child_id]
                if child['kind'] not in ('Term', 'Number', 'Anaphor', 'Syntax'):
                    continue
                slots[name] = {
                    'kind': child['kind'], 'text': child['surface'],
                    'source_spans': deepcopy(child.get('source_spans', [])),
                    'analysis_range': deepcopy(child.get('analysis_range', [])),
                    **({'value': child['value']} if 'value' in child else {}),
                }
            out.append({'kind':n.get('lowering_kind','unclassified'),'public_kind':n.get('public_kind', n['kind']),
                        'slots':slots,'source_spans':deepcopy(n['source_spans']),'analysis_range':deepcopy(n['analysis_range']),
                        'text':n['surface'],'node_id':ident,'production_id':n['production_id'],
                        'attributes':deepcopy(n.get('attributes',{})),'status':'proposed','selection_reason':'token grammar'})
        for root in self.roots:visit(root)
        return out


def syntax_from_candidates(candidates):
    """Materialize reviewed candidates as the current syntax view.

    The normal parser keeps its richer grammar tree.  This adapter is used only
    after a scholar has replaced candidate regions, where the candidate stream
    is the canonical reviewed syntax and every emitted candidate must have a
    corresponding syntax node.
    """
    result = SyntaxResult()
    for candidate in candidates:
        slots = {}
        children = []
        for name, slot in candidate.get('slots', {}).items():
            ident = candidate['node_id'] + ':slot:' + name
            spans = deepcopy(slot.get('source_spans', []))
            analysis_range = deepcopy(slot.get('analysis_range', []))
            grounded = bool(spans) and isinstance(analysis_range, list) and len(analysis_range) == 2
            if not grounded:
                spans, analysis_range = [], []
                result.diagnostics.append({
                    'kind': 'ReviewedSlotMissingExactGrounding', 'node_id': candidate['node_id'],
                    'slot': name, 'reason': slot.get('grounding_diagnostic', 'no_exact_slot_grounding'),
                })
            node = {
                'id': ident,
                'kind': slot.get('kind', 'Term'),
                'slots': {}, 'children': [],
                'source_spans': spans,
                'surface': slot.get('text', ''),
                'analysis_range': analysis_range,
                'production_id': 'REVIEWED_SLOT',
            }
            if 'value' in slot:
                node['value'] = slot['value']
            result.nodes.append(node)
            slots[name] = ident
            children.append(ident)
        public_kind = candidate.get('public_kind')
        if not public_kind:
            result.diagnostics.append({
                'kind': 'ReviewedCandidateMissingPublicKind', 'node_id': candidate['node_id'],
                'reason': 'candidate_has_no_native_public_syntax_kind',
            })
        result.nodes.append({
            'id': candidate['node_id'], 'kind': public_kind or 'ReviewedCandidate', 'public_kind': public_kind,
            'slots': slots, 'children': children,
            'source_spans': deepcopy(candidate.get('source_spans', [])),
            'surface': candidate.get('text', ''),
            'analysis_range': deepcopy(candidate.get('analysis_range', [])),
            'production_id': candidate.get('production_id', 'REVIEWED_CANDIDATE'),
            'lowering_kind': candidate['kind'],
            'attributes': dict(candidate.get('attributes', {})),
        })
        result.roots.append(candidate['node_id'])
        if candidate.get('analysis_range'):
            result.token_coverage.append({'analysis_range': list(candidate['analysis_range']), 'status': 'reviewed'})
    return result
