"""Local construction proposals. No source identity or numerical case dispatch."""
import re
from .inputs import NUMBER, number, span

def propose_constructions(tokens, doc):
    text=doc.get('analysis_text',doc['text']); mapping=doc.get('analysis_to_source',list(range(len(text))))
    result=[]
    def candidate(kind,start,end,slots=None,**attrs):
        item={'kind':kind,'slots':slots or {},'source_spans':[span(doc,mapping[start],mapping[end-1]+1)],'analysis_range':[start,end],'text':text[start:end],'status':'proposed','selection_reason':'local typed slots','attributes':attrs}
        result.append(item);return item
    def slot(m,i):
        x=m.group(i);return {'kind':'Number','text':x,'value':number(x)} if re.fullmatch(NUMBER,x) else {'kind':'Anaphor' if x in ('其','之','其餘') else 'Term','text':x}
    # Punctuation marks boundaries, but paired duration declarations retain both spans.
    mixed_ranges=[]
    pat=r'(?:其[^，,]+?各|中央各)?('+NUMBER+r')日[，,]([^，,．。；;]+?)分之('+NUMBER+r')(?=[．。；;]|$)'
    for m in re.finditer(pat,text):
        candidate('mixed_duration',m.start(),m.end(),{'whole':slot(m,1),'denominator':slot(m,2),'numerator':slot(m,3)},unit='day');mixed_ranges.append((m.start(),m.end()))
    for m in re.finditer(r'[^，,；;．。!！?？]+',text):
        a,b=m.span();raw=m.group()
        if any(a<y and b>x for x,y in mixed_ranges):continue
        # Headings may share their clause with an instruction after a colon.
        head=re.match(r'((?:推|求)[^：:]+)[：:](.+)',raw)
        pieces=[(a,a+len(head.group(1)),head.group(1)),(a+head.start(2),b,head.group(2))] if head else [(a,b,raw)]
        for a,b,raw in pieces:
            patterns=[
                ('update_count',r'加('+NUMBER+r')得一',('increment',)),
                ('numeral_predicate',r'('+NUMBER+r')其(.+)',('factor','value')),
                ('denominator_declaration',r'皆以(.+)為法',('denominator',)),
                ('method_reference',r'(除數如法|數除如法|除命之如前|命之如前)',('reference',)),
                ('count_origin',r'(?:數)?從(.+)起',('origin',)),
                ('receiver_add',r'(?:從|上加)(.+)',('receiver',)),
                ('multiply',r'(?:又|每|餘)?以(.+?)乘(.+)',('left','right')),
                ('subtract',r'以(.+?)減(.+)',('right','left')),
                ('pair_increment',r'(?:加)?(大餘|小餘)('+NUMBER+r')',('receiver','amount')),
                ('load',r'置(.+?)(?:減('+NUMBER+r'))?',('value','decrement')),
                ('divide',r'(.*?)(?:盈|滿)(.+?)得一',('value','divisor')),
                ('cycle_divide',r'(.+?)以(.+?)(?:除去之|除之|去之)',('value','divisor')),
                ('divide_by',r'以(.+?)除(.+)',('divisor','value')),
                ('remainder_name',r'(?:不盈者|不滿|不盡|其餘|餘)(?:名曰|名為|為|則)(.+?)(?:也)?',('label',)),
                ('name',r'(?:名曰|名為)(.+)',('label',)),
                ('task_marker',r'(推|求)(.+)',('marker','target')),
                ('threshold',r'(.*?)(?:滿)?('+NUMBER+r')以上',('value','lower')),
                ('add',r'加('+NUMBER+r')',('amount',)),
                ('loop_threshold',r'盈(.+)',('threshold',)),
                ('concordance_case',r'(?:則|餘則)([天地人]統)(..?)以來年數也',('branch','head')),
                ('mixed_compact',r'(.+?)('+NUMBER+r')日('+NUMBER+r')分',('label','whole','numerator')),
            ]
            found=False
            for kind,pattern,names in patterns:
                match=re.fullmatch(pattern,raw)
                if not match:continue
                slots={name:slot(match,i+1) for i,name in enumerate(names) if match.group(i+1) is not None}
                candidate(kind,a,b,slots);found=True;break
            if not found:candidate('unclassified',a,b)
    return sorted(result,key=lambda c:c['analysis_range'][0])
