"""Typed lexical candidates; every token retains its exact source occurrence."""
import re
from .inputs import NUMBER, number, span

TERMS = ('入統歲數','入蔀積月','入蔀年','統首日','所入蔀名','章閏數','章歲','章法','章月','章中','統法','元法','紀法','蔀法','日法','月法','蔀日','蔀月','中法','日餘','策餘','大餘','小餘','閏餘','積月','積日','太極上元','上元','冬至','中央')

def tokenize_candidates(doc, lexicon):
    text=doc.get('analysis_text',doc['text']); mapping=doc.get('analysis_to_source',list(range(len(text))))
    terms=sorted(set(TERMS)|set(lexicon),key=len,reverse=True)
    pattern=re.compile('|'.join(map(re.escape,terms))+r'|'+NUMBER+r'|如前|如法|其|之|推|求|[，,；;．。：:]|.')
    out=[]
    for m in pattern.finditer(text):
        word=m.group(); kind='Syntax'
        if re.fullmatch(NUMBER,word):kind='Number'
        elif word in terms:kind='FactorReference' if word.endswith('法') else 'Term'
        elif word in ('其','之'):kind='Anaphor'
        elif word in ('推','求'):kind='TaskMarker'
        elif word in ('如法','如前'):kind='MethodReference'
        t={'kind':kind,'text':word,'start':m.start(),'end':m.end(),'source_span':span(doc,mapping[m.start()],mapping[m.end()-1]+1)}
        if kind=='Number':t['value']=number(word)
        out.append(t)
    return out
