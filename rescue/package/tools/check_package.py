"""Verify this specification bundle (and optionally its v3 baseline references).
A successful run is NOT a production parser or transfer test.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

MAIN_DOCS=['RESCUE_START_HERE.md','01_FRONTEND_CONTRACT.md','02_WORK_IMPLEMENTATION_PLAN.md',
           '03_EXPOSED_REGRESSION.md','04_TRANSFER_AND_DECISION.md','05_AUDIT_AND_DELIVERY.md']

def verify(root: Path, repo: Path | None = None) -> dict:
    root=root.resolve();errors=[]
    manifest=json.loads((root/'MANIFEST.json').read_text(encoding='utf8'))
    expected=set()
    for item in manifest['files']:
        path=(root/item['path']).resolve();expected.add(item['path'])
        if not path.is_relative_to(root) or not path.is_file():errors.append('Missing/unsafe bundle file: '+item['path']);continue
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=item['sha256']:errors.append('Bundle hash mismatch: '+item['path'])
    actual_paths={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='MANIFEST.json' and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    if actual_paths!=expected:errors.append('Manifest file set differs: '+str(sorted(actual_paths ^ expected)))
    for name in MAIN_DOCS:
        if name not in expected:errors.append('Missing main document: '+name)
    checks=json.loads((root/'contracts/checks.json').read_text(encoding='utf8'))
    entries=checks['checks']
    if checks.get('count')!=35 or len(entries)!=35:errors.append('Expected 35 specified engineering checks.')
    if len({x['id'] for x in entries})!=len(entries):errors.append('Duplicate check IDs.')
    for x in entries:
        for key in ['id','input_or_setup','must_observe','must_reject_or_contrast','implementation_targets']:
            if not x.get(key):errors.append(x.get('id','unknown')+': missing '+key)
        if x.get('status')!='SPECIFIED_NOT_IMPLEMENTED_IN_THIS_PACKAGE':errors.append('Incorrect production-test completion claim: '+x.get('id','unknown'))
    base_count=0
    if repo is not None:
        repo=repo.resolve()
        upstream=json.loads((root/'contracts/upstream_manifest.json').read_text(encoding='utf8'))
        for x in upstream['files']:
            p=(repo/x['path']).resolve()
            if not p.is_relative_to(repo) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=x['sha256']:
                errors.append('Baseline differs: '+x['path'])
            else:base_count+=1
    return {'ok':not errors,'bundle_files_checked':len(expected),'baseline_files_matched':base_count,
            'specified_engineering_checks':len(entries),'parser_rescue_implemented':False,'fresh_transfer_run':False,'errors':errors}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--repo',type=Path)
    args=ap.parse_args()
    result=verify(args.root,args.repo)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['ok'] else 1)

if __name__=='__main__':main()
