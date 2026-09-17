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
