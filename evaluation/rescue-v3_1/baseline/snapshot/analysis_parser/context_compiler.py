"""Compile source context into declarations and reusable formal method bodies."""
import re
from .lexical import tokenize_candidates
from .construction_ir import propose_constructions
from .inputs import NUMBER,number,span

def compile_context(documents, tables, profile):
    context={'declarations':[],'equivalences':[],'method_library':[],'scope_graph':[],'denominator_declarations':[],'tables':tables,'profile':profile}
    for doc in documents:
        candidates=propose_constructions(tokenize_candidates(doc,{}),doc)
        text=doc.get('analysis_text',doc['text']);mapping=doc.get('analysis_to_source',list(range(len(text))))
        # Scalar declarations are source-local; identical declarations stay separate.
        if doc.get('category')=='context_documents':
            pattern=r'(?:^|[，,．。；;])\s*([^，,．。；;\s零〇一二三四五六七八九十百千萬万0-9]{1,12})[，,]?\s*('+NUMBER+r')(?=[，,．。；;]|$)'
            last=None
            for m in re.finditer(pattern,text):
                label=m.group(1)
                if any(x in label for x in ('推','乘','減','滿','得','除','以')):continue
                d={'id':'decl'+str(len(context['declarations'])+1),'label':label,'value':number(m.group(2)),'source_spans':[span(doc,mapping[m.start(1)],mapping[m.end(2)-1]+1)],'aliases':[]}
                context['declarations'].append(d);last=d
                tail=text[m.end(2):]
                alias=re.match(r'[，,．。]因為([^，,．。；;]+)',tail)
                if alias:d['aliases'].append(alias.group(1))
        cycle=None
        for i,c in enumerate(candidates):
            if c['kind']=='denominator_declaration':context['denominator_declarations'].append(c)
            raw=c['text']
            cm=re.search(r'(積日|大餘|積度)(?:盈|滿|以)('+NUMBER+r')(?:除去之|去之)?$',raw)
            if cm:
                support=list(c['source_spans'])
                complete=raw.endswith(('除去之','去之'))
                if not complete and i+1<len(candidates) and candidates[i+1]['text']=='除之':support+=candidates[i+1]['source_spans'];complete=True
                if complete:cycle={'cycle':number(cm.group(2)),'unit':'du' if cm.group(1)=='積度' else 'day','source_spans':support}
            is_count=c['kind']=='count_origin' and c['slots']['origin']['text'] in ('統首日','所入蔀名','蔀名','角首')
            origin=c['slots']['origin']['text'] if is_count else None
            m=re.fullmatch(r'(?:其餘)?以(所入蔀名|蔀名)命之',raw)
            if m:origin=m.group(1);is_count=True
            if is_count and cycle:
                mid='method'+str(len(context['method_library'])+1)
                context['method_library'].append({'id':mid,'name':'cycle_and_count','formal_inputs':{'offset':{'unit':cycle['unit']},'origin':{'unit':'day_index'},'cycle':{'unit':'integer'}},'returns':{'remainder':'r','result':'day'},'source_spans':cycle['source_spans']+c['source_spans'],'definition_scope':{'tradition':profile.get('tradition'),'doc_id':doc['doc_id']},'origin_label':origin,'cycle_value':cycle['cycle'],'body':[{'id':'reduce','kind':'cycle_reduce','reads':{'dividend':'$offset','divisor':'$cycle'},'writes':{'quotient':'q','remainder':'r'},'source_spans':cycle['source_spans']},{'id':'name','kind':'count','reads':{'offset':'r','origin':'$origin','cycle':'$cycle'},'writes':{'result':'day'},'attributes':{'cyclic':True},'source_spans':c['source_spans']}]})
                cycle=None
    for d in context['declarations']:
        same=[x for x in context['declarations'] if x['id']!=d['id'] and x['label']==d['label'] and x['value']==d['value']]
        if same:context['equivalences'].append({'declaration':d['id'],'equivalent_to':[x['id'] for x in same],'basis':'identical scalar declarations; source identities retained'})
    return context
