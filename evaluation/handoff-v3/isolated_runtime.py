"""Reproducible, reference-free subprocess execution for development and first runs.

The audit hook is an accidental-leakage guard, not a hostile-code OS sandbox.
Only the core package, source packet and initial inputs enter the worker directory.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

EPOCH_INPUTS = {'epoch_elapsed_years', 'epoch_inclusive_year'}
PACKET_FIELDS = {'schema_version', 'input_mode', 'provided_scope', 'primary_documents',
                 'context_documents', 'runtime_policy', 'context_tables',
                 'context_supplied_values', 'selected_profiles', 'event_horizon',
                 'boundary_events', 'generate_event_series'}


def write_exclusive(path, result):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def run_isolated(packet, inputs, *, core_dir, timeout=90):
    unknown = set(packet) - PACKET_FIELDS
    if unknown:
        raise ValueError('Undeclared source packet field: ' + ', '.join(sorted(unknown)))
    if set(inputs) - EPOCH_INPUTS:
        raise ValueError('Only initial epoch inputs are allowed for v3 end-to-end runs')
    with tempfile.TemporaryDirectory(prefix='mathesis-v3-runtime-') as temporary:
        root = Path(temporary)
        shutil.copytree(core_dir, root / 'analysis_parser', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copyfile(__file__, root / 'isolated_runtime.py')
        (root / 'input.json').write_text(json.dumps({'packet': packet, 'inputs': inputs}, ensure_ascii=False), encoding='utf-8')
        result = subprocess.run(
            [sys.executable, '-I', '-X', 'utf8', '-B', str(root / 'isolated_runtime.py'), '--worker'],
            cwd=root, env={'PATH': os.environ.get('PATH', ''), 'LANG': 'C.UTF-8'},
            capture_output=True, encoding='utf-8', timeout=timeout, check=False)
        if result.returncode:
            raise RuntimeError('Isolated runtime process failed: ' + result.stderr[-4000:])
        return json.loads(result.stdout)


def _worker():
    root = Path(__file__).resolve().parent
    # Load standard modules before installing a guard whose own checks must not import.
    import fractions
    import dataclasses
    import re
    core = root / 'analysis_parser'
    stdlib = Path(os.__file__).resolve().parent
    allowed_roots = (core, stdlib)
    input_path = root / 'input.json'
    opened, blocked = [], []

    def within(path, parent):
        return path == parent or parent in path.parents

    def guard(event, args):
        if event in ('open', 'os.listdir', 'os.scandir'):
            raw = args[0]
            if isinstance(raw, int):
                return
            path = Path(os.fsdecode(raw)).resolve()
            allowed = (path == input_path or any(within(path, folder) for folder in allowed_roots)
                       or (event in ('os.listdir', 'os.scandir') and path == root))
            if not allowed:
                blocked.append({'event': event, 'path': str(path)})
                raise PermissionError('File outside runtime source/code allowlist: ' + str(path))
            if event == 'open':
                mode = args[1]
                if isinstance(mode, str) and any(c in mode for c in 'wax+'):
                    blocked.append({'event': event, 'path': str(path), 'mode': mode})
                    raise PermissionError('Runtime inputs and code are read only')
                label = str(path.relative_to(root)) if within(path, root) else 'stdlib/' + str(path.relative_to(stdlib))
                opened.append({'path': label, 'event': event})
        if event.startswith('socket.') or event in ('subprocess.Popen', 'os.system', 'os.exec', 'os.spawn'):
            blocked.append({'event': event})
            raise PermissionError('Runtime external execution/network is blocked')

    sys.addaudithook(guard)
    sys.path.insert(0, str(root))
    payload = json.loads(input_path.read_text(encoding='utf-8'))
    result = {}
    try:
        from analysis_parser.pipeline import parse_packet
        from analysis_parser.execution import execute
        report = parse_packet(payload['packet'])
        execution = execute(report, payload['inputs'])
        result.update(status='completed', report=report, execution=execution)
    except Exception as error:
        result.update(status='runtime_error', error={'type': type(error).__name__, 'message': str(error)})
    result['runtime_audit'] = {
        'policy': 'core-and-input-allowlist-v1',
        'reference_access_blocked': True, 'network_blocked': True,
        'packet_boundary': 'allowlisted source/runtime fields; textual and scholarly context remains declared input, not proof of adversarial semantic purity',
        'opened_files': [dict(item) for item in {x['path']: x for x in opened}.values()],
        'blocked_accesses': blocked,
        'input_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(),
        'python': sys.version,
        'scope': 'Python audit-hook leakage check; not a hostile-code security sandbox',
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    if sys.argv[1:] != ['--worker']:
        raise SystemExit('Use run_isolated from an evaluation runner')
    _worker()
