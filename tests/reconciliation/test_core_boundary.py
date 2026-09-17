"""Integration regressions: public routing and a source-only production install."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ProductionBoundary(unittest.TestCase):
    def test_compiler_and_executor_run_without_evaluation_or_history(self):
        core = ROOT / 'analysis_parser'
        self.assertTrue(core.is_dir(), 'The production compiler has not been reconciled')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(core, root / 'analysis_parser',
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            code = """
import json
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
packet = {'primary_documents': [{'doc_id': 'synthetic.integration',
    'text': '推甲課，置十，以二為法，如法得一，名曰甲量．'}]}
rows = []
for version in ('3.0', '3.1'):
    packet['schema_version'] = version
    report = parse_packet(packet)
    result = execute(report, {})
    rows.append([report.get('ir_revision'), result['named_outputs'], result['unresolved']])
legacy = parse_packet({'primary_documents': []})
print(json.dumps({'rows': rows, 'legacy_revision': legacy.get('ir_revision')}, ensure_ascii=False))
"""
            child = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-c', code],
                                   cwd=root, capture_output=True, encoding='utf-8')
            self.assertEqual(child.returncode, 0, child.stderr)
            actual = json.loads(child.stdout)
            self.assertEqual(actual['rows'], [
                ['3.1-rescue', {'main:甲量': 5}, []],
                ['3.1-rescue', {'main:甲量': 5}, []],
            ])
            self.assertIsNone(actual['legacy_revision'])


if __name__ == '__main__':
    unittest.main()
