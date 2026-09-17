"""Record actual grammar reachability and empty-token counterexamples.

These isolated synthetic parser probes are not historical transfer results.
A failed/unobserved production is disclosed, not silently marked covered.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from analysis_parser.construction_ir import GRAMMAR,_parts,parse_syntax
from analysis_parser.inputs import documents
from analysis_parser.lexical import tokenize_candidates


def check_case(surface,pid):
    doc=documents({'primary_documents':[{'doc_id':'synthetic.inventory','text':surface}]})[0]
    positive=parse_syntax(tokenize_candidates(doc,{}),doc).to_dict()
    negative=parse_syntax([],doc).to_dict()
    return {'surface':surface,'expected_production':pid,'positive_found':any(n['production_id']==pid for n in positive['nodes']),
        'positive_diagnostics':positive['diagnostics'],'negative_rejected':not any(n['production_id']==pid for n in negative['nodes']) and bool(negative['diagnostics']),
        'positive_view':positive,'negative_view':negative}


def build(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);rows=[]
    for i,(kind,public,pattern) in enumerate(GRAMMAR):
        pid=f'G_{kind.upper()}_{i}';parts=_parts(pattern)
        def replacement(match):
            name,typ=match.group(1),match.group(2)
            if typ=='n':return '三'
            if typ=='k':return '推'
            if typ=='b':return '天統'
            if typ=='o':return ''
            if name=='receiver' and kind=='pair_increment':return '大餘'
            if name=='origin':return '甲子'
            return '甲課' if typ=='h' else '甲量' if name in ('left','label','value') else '乙量'
        surface=re.sub(r'\{([^:}]+):([^}]+)\}',replacement,pattern)
        probe=check_case(surface,pid)
        probe_path=out/(pid+'.json');probe_path.write_text(json.dumps(probe,ensure_ascii=False,indent=2)+'\n')
        rows.append({'production_id':pid,'lowering_kind':kind,'ast_kind':public,'pattern':pattern,
            'slots':{x[0]:x[1] for x in parts if isinstance(x,tuple)},'optional_slots':[x[0] for x in parts if isinstance(x,tuple) and x[1]=='o'],
            'optional_suffixes':['并之','從之'] if kind=='multiply' else [],
            'composition':'complete Multiply followed by Combine can form a Sequence; no arbitrary recursive clause composition',
            'type_conditions':{'n':'Number lexical edge','t':'complete bounded Term path excluding undeclared predicate edges','a':'Term or Anaphor','h':'source-bounded heading/name','o':'optional operand','k':'procedure marker','b':'declared Concordance branch'},
            'anaphor_scope':'active Procedure/Query invocation; no cross-definition implicit focus',
            'positive_example':surface,'negative_example':{'surface':surface,'tokens':[]},'positive_reachable':probe['positive_found'],'negative_rejected':probe['negative_rejected'],
            'probe_file':str(probe_path.relative_to(ROOT)),'probe_sha256':hashlib.sha256(probe_path.read_bytes()).hexdigest(),'test_function':'evaluation/rescue-v3_1/production_inventory.py::check_case',
            'qualification_limit':'This is syntax reachability only. Ambiguous/missing positives are not closure-certified. A source qualifier must separately prove types, antecedents, controls, roots, profiles and scoring support.'})
    inventory={'version':'actual-production-inventory-2','implementation_sha256':hashlib.sha256((ROOT/'analysis_parser/construction_ir.py').read_bytes()).hexdigest(),'production_count':len(rows),'productions':rows,
        'composition_productions':[{'production_id':'G_MULTIPLY_COMBINE','slots':['product'],'suffixes':['并之','從之'],'tests':['tests/parser_rescue/test_syntax.py::Syntax.test_L01','tests/parser_rescue/test_syntax.py::Syntax.test_L02','tests/parser_rescue/test_syntax.py::AmbiguityCoverageReview.test_complete_term_competes_with_suffix_composition']},{'production_id':'G_SEQUENCE','ordered_children':['Multiply','Combine'],'tests':['tests/parser_rescue/test_syntax.py::Syntax.test_L01']}],
        'diagnostic_productions':['G_AMBIGUITY','G_UNSUPPORTED'],'summary':{'positive_reachable':sum(r['positive_reachable'] for r in rows),'negative_rejected':sum(r['negative_rejected'] for r in rows)},
        'not_claimed':'Not new historical accuracy or independent scholar adjudication; complete inventory was materialized after A3, not at T0.'}
    (out/'inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n');print(json.dumps(inventory['summary']))
    return inventory

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);build(p.parse_args().out)
