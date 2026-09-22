"""Audit records for native Python branches; no rule registry or inference engine."""
from copy import deepcopy
from functools import lru_cache
import hashlib
import inspect
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=128)
def implementation(function):
    path = Path(inspect.getsourcefile(function)).resolve()
    relative = path.relative_to(ROOT).as_posix()
    lines, first = inspect.getsourcelines(function)
    raw = path.read_bytes()
    try:
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
        committed = subprocess.check_output(['git', 'show', revision + ':' + relative], cwd=ROOT,
                                            stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        revision, committed = locals().get('revision', 'unavailable'), None
    return {'file': relative, 'symbol': function.__qualname__, 'revision': revision,
            'content_sha256': hashlib.sha256(raw).hexdigest(),
            'code_state': 'committed' if committed == raw else 'working_tree',
            'line': first, 'end_line': first + len(lines) - 1, 'source': ''.join(lines)}


def condition(key, actual, expected=True):
    """Evaluate equality once. Call sites supply actual native Python operands."""
    return {'key': key, 'operator': 'equals', 'expected': expected,
            'actual': actual, 'matched': actual == expected}


def rule(rule_id, stage, conditions, function, *, result, otherwise=None, subject=None):
    """The returned matched flag is consumed by the real branch, then by the UI."""
    matched = all(row['matched'] for row in conditions)
    return {'schema': 'RuleTrace/1', 'rule_id': rule_id, 'stage': stage,
            'conditions': deepcopy(conditions), 'matched': matched,
            'result': deepcopy(result if matched else otherwise or {'result_class': 'no_match'}),
            'subject': deepcopy(subject or {}), 'implementation': implementation(function)}
