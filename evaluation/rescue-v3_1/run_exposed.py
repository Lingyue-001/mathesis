"""Immutable checkpoint runner for the four already exposed development windows."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
import runtime_protocol as runtime
import fixed_scoring as scoring
from chain_gate import assess


def run(out, *, source_asset_paths=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    before=runtime.manifest(ROOT,source_asset_paths=source_asset_paths)
    for record in before['files']:
        target=out/'snapshot'/record['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/record['path'],target)
    runtime.exclusive(out/'behavior_manifest.json',before)
    contracts=json.loads((HERE/'contracts/chain_contracts.json').read_text(encoding='utf-8'));rows=[]
    for name in ('A01','A02','A03','A04'):
        payload=json.loads((HERE/'development_packets'/f'{name}.json').read_text(encoding='utf-8'))
        runtime.exclusive(out/'inputs'/f'{name}.json',payload)
        result=runtime.run_isolated(payload['packet'],payload['inputs'],core_dir=ROOT/'analysis_parser')
        runtime.exclusive(out/f'{name}.json',result)
        # Runtime error remains a full fixed-denominator failure, never dropped.
        report=result.get('report',{'events':[],'value_instances':[],'unresolved':[{'cause':'runtime_failed'}]})
        execution=result.get('execution',{'unresolved':[{'cause':'runtime_failed'}]})
        reference=json.loads((HERE/'registered_references'/f'{name}.json').read_text(encoding='utf-8'))
        score=scoring.evaluate(payload['packet'],report,reference,execution=execution,auxiliary=result)
        chain=assess(payload['packet'],report,execution,score,contracts[name],scoring.Graph)
        score.update(full_chain_passed=chain['full_chain_passed'],full_chain_note='Independent chain gate attached',chain_gate=chain)
        runtime.exclusive(out/f'{name}.score.json',score)
        rows.append({'window_id':name,'runtime_status':result['status'],'obligations_passed':sum(o['status']=='pass' for o in score['obligations']),
            'obligations_total':len(score['obligations']),'relations':score['relations'],'full_chain_passed':chain['full_chain_passed'],
            'runtime_guard_clean':not result.get('runtime_audit',{}).get('blocked_accesses')})
    changed=runtime.verify(ROOT,before)
    summary={'phase':'exposed_development','new_transfer_evidence':False,'windows':rows,'behavior_changes_during_run':changed,
        'all_passed':not changed and all(r['runtime_status']=='completed' and r['runtime_guard_clean'] and r['full_chain_passed'] and r['obligations_passed']==r['obligations_total'] for r in rows)}
    runtime.exclusive(out/'summary.json',summary)
    files=[{'path':str(p.relative_to(out)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.rglob('*')) if p.is_file()]
    runtime.exclusive(out/'manifest.json',{'files':files,'outputs_exclusively_created':True})
    print(json.dumps(summary,ensure_ascii=False));return 0 if summary['all_passed'] else 1

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--source-asset-map',type=Path,help='JSON mapping of frozen source paths to local paths; identities remain mandatory')
    args=ap.parse_args()
    mapping=json.loads(args.source_asset_map.read_text(encoding='utf-8')) if args.source_asset_map else None
    raise SystemExit(run(args.out,source_asset_paths=mapping))
