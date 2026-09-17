"""Fail-closed project decision arithmetic, not a semantic parser evaluator.

This tool checks a reviewed evidence summary. True flags must be supported by the
actual frozen logs/graphs; the tool cannot establish their scholarly correctness.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any


def decide(payload: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    def result(decision: str, reasons: list[str], **details: Any) -> dict[str, Any]:
        return {'decision': decision, 'reasons': reasons,
                'scope': 'engineering budget gate; not a statistical or universal impossibility claim',
                'semantic_evidence_verified_by_this_tool': False, **details}
    if not isinstance(payload, dict):
        return result('INCONCLUSIVE_PROTOCOL', ['Summary must be an object.'])
    if payload.get('status') == 'NOT_RUN':
        return result('NOT_RUN', ['Template or unexecuted experiment.'])
    errors=[]
    if payload.get('status') != 'EVALUATED': errors.append('status must be EVALUATED.')
    if payload.get('protocol_version') != policy['version']: errors.append('Protocol version mismatch.')
    pre=payload.get('preconditions', {})
    for key in policy['required_preconditions']:
        if not isinstance(pre,dict) or pre.get(key) is not True:
            errors.append('Unverified precondition: '+key)
    evidence=payload.get('evidence_files')
    if not isinstance(evidence,list) or not evidence:
        errors.append('Nonempty evidence_files required.')
    else:
        for item in evidence:
            if not isinstance(item,dict) or not isinstance(item.get('path'),str) or not item['path'] or not re.fullmatch(r'[0-9a-f]{64}',str(item.get('sha256',''))):
                errors.append('Each evidence file needs a path and SHA-256.')
    cases=payload.get('cases')
    if not isinstance(cases,list): errors.append('cases must be a list.'); cases=[]
    if errors: return result('INCONCLUSIVE_PROTOCOL',errors)
    target=policy['a_prime_cases']
    if len(cases)<target:
        return result('INSUFFICIENT_ELIGIBLE_MATERIAL',[f'{len(cases)}/{target} A-prime cases available.'])
    if len(cases)>target:
        return result('INCONCLUSIVE_PROTOCOL',['Unregistered extra A-prime cases.'])
    ids=[];total=passed=complete=structural_failed=0
    for i,c in enumerate(cases):
        if not isinstance(c,dict): errors.append(f'Case {i} is not an object.');continue
        cid=c.get('case_id');ids.append(cid)
        if not isinstance(cid,str) or not cid: errors.append(f'Case {i}: invalid case_id.')
        closures=c.get('closures',{})
        for field in policy['required_case_closures']:
            if not isinstance(closures,dict) or closures.get(field) is not True:
                errors.append(f'{cid}: closure unverified: {field}')
        booleans=policy['structural_fields']+['execution_ok','source_coverage_ok','full_chain']
        for field in booleans:
            if type(c.get(field)) is not bool: errors.append(f'{cid}: {field} must be Boolean.')
        n=c.get('obligations_total');p=c.get('obligations_passed');u=c.get('relevant_unresolved')
        if type(n) is not int or type(p) is not int or n<=0 or not 0<=p<=n:
            errors.append(f'{cid}: invalid obligation counts.');continue
        if type(u) is not int or u<0:
            errors.append(f'{cid}: invalid unresolved count.');continue
        good_structure=all(c.get(k) is True for k in policy['structural_fields'])
        if c.get('full_chain') is True and not (p==n and good_structure and c.get('execution_ok') is True and c.get('source_coverage_ok') is True and u==0):
            errors.append(f'{cid}: full-chain claim contradicts its evidence summary.')
        total+=n;passed+=p;complete+=int(c.get('full_chain') is True)
        structural_failed+=int(not good_structure)
    if any(not isinstance(x,str) for x in ids) or len(set(x for x in ids if isinstance(x,str)))!=len(ids):
        errors.append('Missing or duplicate case identities.')
    if errors:return result('INCONCLUSIVE_PROTOCOL',errors)
    details={'complete_chains':complete,'case_count':target,'obligations_passed':passed,
             'obligations_total':total,'structural_failed_cases':structural_failed}
    threshold=policy['continue_min_obligation_fraction']
    enough=passed*threshold['denominator']>=total*threshold['numerator']
    if structural_failed==0 and complete>=policy['continue_min_complete_chains'] and enough:
        return result('CONTINUE_BOUNDED_AUTOMATION', ['Registered A-prime engineering gate met; B-prime coverage remains separate.'],**details)
    if complete<=policy['stop_max_complete_chains'] or structural_failed>=policy['stop_min_structural_failed_cases']:
        return result('STOP_DEFAULT_AUTOMATION',['Registered stopping threshold reached. Preserve artifacts; do not repair the first-run score.'],**details)
    return result('BORDERLINE_STOP_DEFAULT',['Some progress but continuation gate not met. No automatic extra repair round.'],**details)


def verify_evidence_files(payload: dict[str, Any], root: Path) -> list[str]:
    root=root.resolve();errors=[]
    for item in payload.get('evidence_files',[]):
        if not isinstance(item,dict) or not isinstance(item.get('path'),str):
            errors.append('Malformed evidence file entry.');continue
        path=(root/item['path']).resolve()
        if not path.is_relative_to(root):
            errors.append('Evidence path escapes root: '+item['path']);continue
        if not path.is_file():errors.append('Evidence file missing: '+item['path']);continue
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=item.get('sha256'):errors.append('Evidence hash mismatch: '+item['path'])
    return errors


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('summary',type=Path)
    ap.add_argument('--policy',type=Path,default=Path(__file__).resolve().parents[1]/'contracts/decision_policy.json')
    ap.add_argument('--evidence-root',type=Path,help='Required for EVALUATED summaries; checks cited file hashes.')
    ap.add_argument('--out',type=Path,help='Exclusive-create result file; existing paths are rejected.')
    args=ap.parse_args()
    try:
        payload=json.loads(args.summary.read_text(encoding='utf8'))
        policy=json.loads(args.policy.read_text(encoding='utf8'))
        verdict=decide(payload,policy)
        if isinstance(payload,dict) and payload.get('status')=='EVALUATED':
            errors=['--evidence-root required for evaluated summaries.'] if args.evidence_root is None else verify_evidence_files(payload,args.evidence_root)
            if errors:verdict={'decision':'INCONCLUSIVE_PROTOCOL','reasons':errors,'semantic_evidence_verified_by_this_tool':False}
        text=json.dumps(verdict,ensure_ascii=False,indent=2)+'\n'
        if args.out:
            args.out.parent.mkdir(parents=True,exist_ok=True)
            with args.out.open('x',encoding='utf8') as f:f.write(text)
        print(text,end='')
    except (OSError,ValueError,TypeError,KeyError) as error:
        raise SystemExit('Input/output validation failed: '+str(error)) from error

if __name__=='__main__':main()
