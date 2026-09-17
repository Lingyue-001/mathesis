"""Token-derived syntax, including alternatives and source coverage."""
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
            slots={k:{'kind':by_id[v]['kind'],'text':by_id[v]['surface'],**({'value':by_id[v]['value']} if 'value' in by_id[v] else {})} for k,v in n['slots'].items() if by_id[v]['kind'] in ('Term','Number','Anaphor','Syntax')}
            out.append({'kind':n.get('lowering_kind','unclassified'),'slots':slots,'source_spans':n['source_spans'],'analysis_range':n['analysis_range'],'text':n['surface'],'node_id':ident,'production_id':n['production_id'],'attributes':n.get('attributes',{}),'status':'proposed','selection_reason':'token grammar'})
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
            node = {
                'id': ident,
                'kind': slot.get('kind', 'Term'),
                'slots': {}, 'children': [],
                'source_spans': list(candidate.get('source_spans', [])),
                'surface': slot.get('text', ''),
                'analysis_range': list(candidate.get('analysis_range', [])),
                'production_id': 'REVIEWED_SLOT',
            }
            if 'value' in slot:
                node['value'] = slot['value']
            result.nodes.append(node)
            slots[name] = ident
            children.append(ident)
        result.nodes.append({
            'id': candidate['node_id'], 'kind': candidate['kind'].title(),
            'slots': slots, 'children': children,
            'source_spans': list(candidate.get('source_spans', [])),
            'surface': candidate.get('text', ''),
            'analysis_range': list(candidate.get('analysis_range', [])),
            'production_id': candidate.get('production_id', 'REVIEWED_CANDIDATE'),
            'lowering_kind': candidate['kind'],
            'attributes': dict(candidate.get('attributes', {})),
        })
        result.roots.append(candidate['node_id'])
        if candidate.get('analysis_range'):
            result.token_coverage.append({'analysis_range': list(candidate['analysis_range']), 'status': 'reviewed'})
    return result
