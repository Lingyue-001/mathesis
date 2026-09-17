"""A finite compositional grammar over candidate-token paths.

Patterns are terminal strings and typed slots, never regular expressions over
source clauses. A slot consumes complete lexical edges; predicate edges cannot
become terms. All successful derivations survive until structural deduplication.
"""
from .syntax_ir import SyntaxResult

# (lowering kind, public AST kind, grammar pattern). Slots use n:number,
# t:bounded term, a:term/anaphor, h:heading/name and o:optional operand.
GRAMMAR=[
 ('task_marker','Heading','{marker:k}{target:h}'),
 ('query_marker','Heading','欲知{target:h}'),
 ('update_count','RepeatStep','加{increment:n}得一'),
 ('numeral_predicate','Multiply','{factor:n}其{value:t}'),
 ('denominator_declaration','DenominatorDeclaration','皆以{denominator:a}為法'),
 ('denominator_declaration','DenominatorDeclaration','以{denominator:a}為法'),
 ('multiply','Multiply','以{left:a}乘{right:a}'),
 ('multiply','Multiply','又以{left:a}乘{right:a}'),
 ('multiply','Multiply','每以{left:a}乘{right:a}'),
 ('multiply','Multiply','餘以{left:a}乘{right:a}'),
 ('subtract','Subtract','以{right:a}減{left:a}'),
 ('update','Update','加{amount:a}於{receiver:t}'),
 ('pair_increment','Increment','加{receiver:t}{amount:n}'),
 ('pair_increment','Increment','{receiver:t}{amount:n}'),
 ('load','Load','置{value:a}減{decrement:n}'),
 ('load','Load','置{value:a}'),
 ('divide','DivMod','{value:o}盈{divisor:a}得一'),
 ('divide','DivMod','{value:o}滿{divisor:a}得一'),
 ('cycle_divide','CycleReduce','{value:a}以{divisor:a}除去之'),
 ('cycle_divide','CycleReduce','{value:a}以{divisor:a}去之'),
 ('cycle_divide','CycleReduce','{value:a}盈{divisor:a}除去之'),
 ('cycle_divide','CycleReduce','{value:a}滿{divisor:a}除去之'),
 ('divide_by','CycleReduce','以{divisor:a}除{value:a}'),
 ('pending_cycle','PendingCycle','{value:a}盈{divisor:a}'),
 ('pending_cycle','PendingCycle','{value:a}滿{divisor:a}'),
 ('loop_threshold','LoopThreshold','盈{threshold:a}'),
 ('remainder_name','NameRemainder','不盈者名曰{label:t}'),
 ('remainder_name','NameRemainder','不盈者為{label:t}'),
 ('remainder_name','NameRemainder','不滿為{label:t}'),
 ('remainder_name','NameRemainder','不盡為{label:t}'),
 ('remainder_name','NameRemainder','其餘為{label:t}'),
 ('remainder_name','NameRemainder','餘為{label:t}'),
 ('remainder_name','NameRemainder','餘則{label:t}'),
 ('name','Name','名曰{label:t}'),('name','Name','名為{label:t}'),('name','Name','為{label:t}'),
 ('receiver_add','Combine','從{receiver:a}'),('receiver_add','Combine','上加{receiver:a}'),('receiver_add','Combine','并{receiver:a}'),
 ('count_origin','Count','從{origin:h}起'),('count_origin','Count','數從{origin:h}起'),
 ('count_origin','Count','中數從{origin:h}起'),('count_origin','Count','次數從{origin:h}起'),
 ('count_command','Count','以{origin:a}命之'),('count_command','Count','其餘以{origin:a}命之'),
 ('threshold','Threshold','{value:o}{lower:n}以上'),('threshold','Threshold','{value:o}滿{lower:n}以上'),
 ('add','Add','加{amount:a}'),('recur_increment','Increment','又加{receiver:t}{amount:n}'),
 ('double_interval','DoubleInterval','倍{target:h}'),
 ('mixed_compact','MixedDuration','{label:t}{whole:n}日{numerator:n}分'),
 ('declaration','Declaration','{label:t}{value:n}'),
 ('declaration','Declaration','{label:t}，{value:n}'),
 ('parameter_alias','ParameterAlias','因為{label:t}'),
 ('mixed_duration','MixedDuration','{whole:n}日，{denominator:a}分之{numerator:n}'),
 ('mixed_duration','MixedDuration','其{subject:h}各{whole:n}日，{denominator:a}分之{numerator:n}'),
 ('mixed_duration','MixedDuration','中央各{whole:n}日，{denominator:a}分之{numerator:n}'),
 ('name','Name','則{label:t}也'),
 ('remainder_name','NameRemainder','餘名曰{label:t}'),
 ('remainder_name','NameRemainder','餘則{label:t}也'),
 ('multiply_focus','Multiply','乘{factor:a}'),
 ('reuse_operation','ReuseOperation','{receiver:t}亦如之'),
 ('multiply','Multiply','不盈者以{left:a}乘{right:a}'),
 ('epoch_load','EpochLoad','置上元以來'),
 ('pair_increment','Increment','{receiver:t}加{amount:n}'),
 ('recur_increment','Increment','當加{receiver:t}{amount:n}'),
 ('receiver_add','Combine','并之{receiver:t}'),
 ('method_value_reference','MethodCall','數除{value:t}如法'),
 ('count_remainder','Count','不盈者數起於{origin:h}'),
 ('scalar_value','ScalarDeclaration','為{value:n}'),
 ('scalar_name','ScalarName','是為{label:t}'),
 ('schedule_row','ScheduleRow','{year:n}歲{count:n}閏'),
 ('scan_length','ScanLength','除{months:n}'),
 ('epoch_load','EpochLoad','置太極上元以來'),('epoch_divide','EpochDivide','以{divisor:a}除去上元'),
 ('entry_cycle','EntryCycle','盈{divisor:a}除之'),
 ('entry_remainder_divide','EntryRemainderDivide','其餘以{divisor:a}除之'),
 ('concordance_case','ConcordanceCase','則{branch:b}{head:t}以來年數也'),
 ('concordance_case','ConcordanceCase','餘則{branch:b}{head:t}以來年數也'),
 ('conditional_count','ConditionalCount','滿{lower:n}以上亦得一筭之數'),
]
EXACT={
 'method_reference':('除數如法','數除如法','除命之如前','命之如前'),
 'use_denominator':('如法得一',), 'complete_cycle':('除之','除去之'),
 'reuse_operation':(),
 'judgment':('歲有閏','其歲有閏','其月大'),
 'epoch_inclusive':('盡所求年',),'epoch_elapsed':('外所求年',),'concordance_remainder':('餘不盈統者',),
 'concordance_pending':('盈統','又盈統'), 'concordance_select':('各以其統首日為紀',),
 'era_index':('所得數從天紀',),'obscuration_index':('所得數從甲子蔀起',),
 'year_name':('即所求年太歲所在',),'nominal':('起冬至',),
 'loop_result':('數所得',),'temporal_anchor':('冬至後',),
 'boundary':('中氣在朔若二日','或進退','以中氣定之'),
 'annotation':('算盡之外','餘不盈者','至有閏之歲','入章','月大','算外','則中至終閏盈','則前月閏也','閏月也','筭盡之外','則所求冬至日也','則前年冬至之日也','小寒日也','則朔日也','則前年天正十一月朔日也','筭外則所入紀也','不滿紀法者','入紀年數也','筭外','筭上','所入蔀也不滿蔀法者','所入蔀也不滿蔀法者入蔀年數也各以所入蔀歲名命之')}
for kind,words in EXACT.items():
    for word in words:GRAMMAR.append((kind, ''.join(x.title() for x in kind.split('_')),word))


def _parts(pattern):
    parts=[]
    while pattern:
        if pattern.startswith('{'):
            end=pattern.index('}');name,typ=pattern[1:end].split(':');parts.append((name,typ));pattern=pattern[end+1:]
        else:
            end=pattern.find('{');end=len(pattern) if end<0 else end;parts.append(pattern[:end]);pattern=pattern[end:]
    return parts
RULES=[(kind,public,pattern,_parts(pattern)) for kind,public,pattern in GRAMMAR]


def parse_syntax(tokens,doc):
    result=SyntaxResult();text=doc.get('analysis_text',doc['text']);edges={}
    for t in tokens:
        a,b=t.get('start',-1),t.get('end',-1)
        if 0<=a<b<=len(text) and text[a:b]==t.get('text'):edges.setdefault(a,[]).append(t)
        else:result.diagnostics.append({'kind':'InvalidToken','token':t})
    def node(kind,a,b,slots=None,children=None,production='LEXICAL',**attrs):
        from .inputs import span
        mapping=doc.get('analysis_to_source',list(range(len(text))))
        ident=doc['doc_id']+':ast'+str(len(result.nodes)+1)
        n={'id':ident,'kind':kind,'slots':slots or {},'children':children or [],'source_spans':[span(doc,mapping[a],mapping[b-1]+1)] if a<b else [],'surface':text[a:b],'analysis_range':[a,b],'production_id':production,**attrs};result.nodes.append(n);return ident
    def literal(pos,word,end):
        if not word:return [pos]
        found=[]
        for t in edges.get(pos,[]):
            if t['end']<=end and word.startswith(t['text']):found+=literal(t['end'],word[len(t['text']):],end)
        return list(set(found))
    def slot_paths(pos,typ,end):
        if typ=='o':yield pos,[]
        def walk(p,path):
            if p>=end:return
            for t in edges.get(p,[]):
                if t['end']>end:continue
                good=t['kind'] in ('Term','FactorReference')
                if typ=='n':good=t['kind']=='Number'
                elif typ=='k':good=t['text'] in ('推','求')
                elif typ=='b':good=t['text'] in ('天統','地統','人統')
                elif typ=='h':good=t['text'] not in '，,；;．。：:'
                elif typ in ('a','o'):good=good or t['kind'] in ('Number','Anaphor')
                if not good:continue
                new=path+[t];yield t['end'],new
                if typ not in ('n','k','b') and not (t['kind']=='Anaphor' and t['text']=='之'):yield from walk(t['end'],new)
        yield from walk(pos,[])
    def matches(start,end):
        found=[]
        for kind,public,pattern,parts in RULES:
            def advance(i,pos,slots):
                if i==len(parts):
                    if pos==end:found.append((kind,public,pattern,slots))
                    return
                part=parts[i]
                if isinstance(part,str):
                    for q in literal(pos,part,end):advance(i+1,q,slots)
                else:
                    key,typ=part
                    for q,path in slot_paths(pos,typ,end):advance(i+1,q,{**slots,key:(pos,q,path)})
            advance(0,start,{})
        # Declaration/pair numeric forms are lexically indistinguishable; explicit
        # size-remainder role selects increment, others are declarations.
        if any(f[0]=='annotation' for f in found):found=[f for f in found if f[0]!='name']
        filtered=[]
        for f in found:
            k,_,_,s=f
            if k=='pair_increment' and text[start:start+1]!='加' and '加' not in text[start:end] and text[s['receiver'][0]:s['receiver'][1]] not in ('大餘','小餘'):continue
            if k=='declaration' and text[s['label'][0]:s['label'][1]] in ('大餘','小餘'):continue
            # numeral anaphor predicate is not plain add/load segmentation.
            if k=='add' and any(g[0]=='pair_increment' for g in found):continue
            filtered.append(f)
        unique={}
        for f in filtered:
            key=(f[0],tuple((k,a,b) for k,(a,b,path) in f[3].items()))
            unique[key]=f
        return list(unique.values())
    def build(match,a,b):
        kind,public,pattern,slots=match;ids={}
        for name,(x,y,path) in slots.items():
            leafkind='Number' if len(path)==1 and path[0]['kind']=='Number' else 'Anaphor' if path and path[0]['kind']=='Anaphor' else 'Term'
            if kind=='numeral_predicate' and name=='value':leafkind='Anaphor'
            ids[name]=node(leafkind,x,y,production='LEX_'+leafkind.upper(),**({'value':path[0]['value']} if leafkind=='Number' else {}))
        return node(public,a,b,ids,list(ids.values()),'G_'+kind.upper()+'_'+str(GRAMMAR.index((kind,public,pattern))),lowering_kind=kind,attributes={'continuation':pattern.startswith('餘以')})
    # Clause boundaries are token edges, not a second text parser. Commas may
    # participate in the explicit mixed-duration production.
    breaks=[0]+[i+1 for i,c in enumerate(text) if c in '，,；;．。：:']+[len(text)]
    ranges=[]
    for a,b in zip(breaks,breaks[1:]):
        while a<b and text[a].isspace():a+=1
        while b>a and (text[b-1].isspace() or text[b-1] in '，,；;．。：:'):b-=1
        if a<b:ranges.append((a,b))
    i=0
    while i<len(ranges):
        a,b=ranges[i];ms=[]
        if i+1<len(ranges):
            x,y=ranges[i+1];ms=[m for m in matches(a,y) if m[0] in ('mixed_duration','declaration')]
            if ms:b=y;i+=1
        if not ms:ms=matches(a,b)
        if any(n.get('lowering_kind')=='concordance_remainder' for n in result.nodes) and any(m[0]=='concordance_pending' for m in ms):
            ms=[m for m in ms if m[0]=='concordance_pending']
        # Compose only complete prefix productions and complete suffix terminals.
        compositions=[]
        for cut in sorted(edges):
            if not a<cut<b:continue
            for suffix in ('并之','從之'):
                if b in literal(cut,suffix,b):
                    for m in matches(a,cut):
                        if m[0]=='multiply':compositions.append((m,cut,suffix))
        # Whole-term and composed derivations compete on equal terms. No
        # grammar ordering or preference for a suffix can erase a legal parse.
        alternatives=[build(m,a,b) for m in ms]
        for m,cut,suffix in compositions:
            mul=build(m,a,cut)
            comb=node('Combine',cut,b,{'product':mul},[mul],'G_MULTIPLY_COMBINE',lowering_kind='combine_product')
            alternatives.append(node('Sequence',a,b,children=[mul,comb],production='G_SEQUENCE'))
        if len(alternatives)==1:
            result.roots.append(alternatives[0]);coverage_status='parsed'
        elif len(alternatives)>1:
            result.roots.append(node('AmbiguousParse',a,b,children=alternatives,production='G_AMBIGUITY'))
            result.diagnostics.append({'kind':'AmbiguousParse','analysis_range':[a,b],'alternatives':alternatives})
            coverage_status='unresolved'
        else:
            ident=node('UnsupportedConstruction',a,b,production='G_UNSUPPORTED');result.roots.append(ident)
            result.diagnostics.append({'kind':'UnsupportedConstruction','analysis_range':[a,b],'node_id':ident})
            coverage_status='unresolved'
        result.token_coverage.append({'analysis_range':[a,b],'status':coverage_status})
        i+=1
    owned={pos for region in result.token_coverage for pos in range(*region['analysis_range'])}
    for pos,ch in enumerate(text):
        if pos not in owned and (ch.isspace() or ch in '，,；;．。：:'):
            result.token_coverage.append({'analysis_range':[pos,pos+1],'status':'registered_noncomputational'})
    if text and not ranges:result.diagnostics.append({'kind':'EmptyCoverage'})
    return result

def propose_constructions(tokens,doc):
    return parse_syntax(tokens,doc).candidates()
