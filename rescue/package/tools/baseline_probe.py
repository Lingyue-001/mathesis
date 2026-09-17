"""Read-only v3 replay and intentionally synthetic front-end diagnostics.
Never selects unseen historical text. Outputs are replay, not transfer results.
"""
from __future__ import annotations
import argparse, copy, hashlib, importlib.util, json, sys
from pathlib import Path

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();root=args.repo.resolve()
    if args.out.exists(): raise SystemExit('Output exists: use a new replay path.')
    core=root/'analysis_parser'
    before={str(p.relative_to(root)):sha(p) for p in core.glob('*.py')}
    sys.path.insert(0,str(root))
    from analysis_parser.inputs import documents
    from analysis_parser.lexical import tokenize_candidates
    from analysis_parser.construction_ir import propose_constructions
    from analysis_parser.context_compiler import compile_context
    from analysis_parser.pipeline import parse_packet
    runner=root/'evaluation/handoff-v3/isolated_runtime.py'
    spec=importlib.util.spec_from_file_location('rescue_v3_runner',runner)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    folder=root/'evaluation/handoff-v3/prospective'
    replays=[]
    for name in ['A01','A02','A03','A04']:
        item=json.loads((folder/'packets'/f'{name}.json').read_text())
        expected=json.loads((folder/'first_outputs'/f'{name}.json').read_text())
        actual=mod.run_isolated(item['packet'],item['inputs'],core_dir=core)
        rep=actual.get('report',{});exe=actual.get('execution',{})
        invalid_terms=[v.get('labels',[]) for v in rep.get('value_instances',[]) if any(('并之' in lab or '於' in lab) for lab in v.get('labels',[]))]
        replays.append({'case':name,'report_equal_to_saved':rep==expected.get('report'), 'execution_equal_to_saved':exe==expected.get('execution'), 'scope_count':len(rep.get('scope_graph',[])), 'task_export_keys':list(rep.get('task_exports',{})), 'execution_unresolved':len(exe.get('unresolved',[])),'compound_terms':invalid_terms})
    def doc(text,category='primary_documents'):
        return documents({category:[{'doc_id':'synthetic.rescue','text':text}]})[0]
    d=doc('以甲法乘其乙餘并之')
    t=tokenize_candidates(d,{})
    with_tokens=propose_constructions(t,d)
    no_tokens=propose_constructions([],d)
    add=propose_constructions(tokenize_candidates(doc('加甲量於乙量'),{}),doc('加甲量於乙量'))
    ctx=compile_context([doc('甲法三．置乙量五．加大餘二十九．積日盈六十，除之．','context_documents')],[],{})
    sample=json.loads((folder/'packets/A01.json').read_text())['packet']
    sample=copy.deepcopy(sample); sample['context_documents']=[]
    frames=[]
    for title in ['冬至','甲課']:
        sample['primary_documents']=[{'doc_id':'synthetic.frame','text':f'推{title}，置甲量．'}]
        rep=parse_packet(sample)
        frames.append({'title':title,'scope_count':len(rep.get('scope_graph',[])),'scope_graph':rep.get('scope_graph',[])})
    result={'kind':'v3_replay_and_synthetic_diagnostic_NOT_new_transfer','python':sys.version,'replays':replays,
      'synthetic':{'compound_multiply':with_tokens,'tokens_ignored_same_output_with_empty_list':with_tokens==no_tokens,'recipient_add':add,'imperatives_misread_as_declarations':[{'label':d['label'],'value':d['value']} for d in ctx['declarations']], 'known_vs_unknown_title_frames':frames},
      'core_hashes_unchanged':before=={str(p.relative_to(root)):sha(p) for p in core.glob('*.py')}, 'core_hashes':before}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'replays':replays,'tokens_ignored':result['synthetic']['tokens_ignored_same_output_with_empty_list'],'declarations':result['synthetic']['imperatives_misread_as_declarations'],'scope_counts':[(x['title'],x['scope_count']) for x in frames],'core_hashes_unchanged':result['core_hashes_unchanged']},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
