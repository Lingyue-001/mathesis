"""Overlapping lexical edges; all candidates retain exact source occurrences."""
import re
from .inputs import NUMBER, number, span
TERMS=('入統歲數','入蔀積月','入蔀年','統首日','所入蔀名','章閏數','章歲','章法','章月','章中','統法','元法','紀法','蔀法','日法','月法','蔀日','蔀月','中法','日餘','策餘','大餘','小餘','閏餘','積月','積日','太極上元','上元','冬至','中央','蔀名','天統','地統','人統','見復數','歲數','歲星歲數','定見復數','見復餘','見中分','見中法','積中','中餘','元中','中元餘','入章中數','星見中次','閏分','見閏分','見月法','見月日法','月餘','後月餘','月元餘','入章月數','入月日數','積次','次餘','定次','統首','太歲日','星所見月','後見月','見日','所在次','星見月朔日','見數')
# Operators bound opaque terms. A declared whole word may still contain them.
BOUNDARY=set('不者則也命各來以乘減加於于并從上置盈滿得為名曰除去起求推其之亦又每皆倍，,；;．。：:日分零〇一二三四五六七八九十百千萬万0123456789')
def tokenize_candidates(doc,lexicon):
    text=doc.get('analysis_text',doc['text']);mapping=doc.get('analysis_to_source',list(range(len(text))))
    terms=set(TERMS)|set(lexicon)
    # Lexical declaration recognition only introduces whole-word candidates.
    for m in re.finditer(r'(?:^|[，,．。；;])([^，,．。；;\s零〇一二三四五六七八九十百千萬万0123456789]+?)('+NUMBER+r')(?=[，,．。；;]|$)',text):
        if not any(x in m.group(1) for x in ('置','加','盈','推','求','以','得','除','乘','為','分之')):terms.add(m.group(1))
    out=[];seen=set()
    def add(a,b,kind):
        if (a,b,kind) in seen:return
        seen.add((a,b,kind));word=text[a:b]
        t={'kind':kind,'text':word,'start':a,'end':b,'source_span':span(doc,mapping[a],mapping[b-1]+1)}
        if kind=='Number':t['value']=number(word)
        out.append(t)
    for i,ch in enumerate(text):
        if ch.isspace():continue
        for term in terms:
            if text.startswith(term,i):add(i,i+len(term),'Term')
        n=re.match(NUMBER,text[i:])
        if n:add(i,i+n.end(),'Number')
        add(i,i+1,'Syntax')
        if ch in BOUNDARY:add(i,i+1,'Anaphor' if ch in '其之' else 'Syntax')
        else:
            j=i+1
            while j<len(text) and text[j] not in BOUNDARY and not text[j].isspace():j+=1
            add(i,j,'Term')
    return sorted(out,key=lambda t:(t['start'],t['end'],t['kind']))
