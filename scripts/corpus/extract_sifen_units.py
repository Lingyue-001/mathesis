#!/usr/bin/env python3
"""Rebuild any registered corpus workspace (historical command name retained).

This command reads only the registered corpus and explicit review overrides.
It does not import the parser, evaluator, Pattern Lab, or adjudication code.
"""
import argparse
import json
from pathlib import Path
import sys


REPOSITORY = Path(__file__).resolve().parents[2]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from source_adapters.corpus_review import regenerate, migrate_rules


def main():
    parser = argparse.ArgumentParser(description='Rebuild a registered corpus review workspace.')
    parser.add_argument('--root', type=Path, default=REPOSITORY)
    parser.add_argument('--source-id', default='sifen')
    parser.add_argument('--output-dir', type=Path)
    migration = parser.add_mutually_exclusive_group()
    migration.add_argument('--migration-report', action='store_true', help='Report exact-span rule changes without replacing workspace files.')
    migration.add_argument('--migrate-rules', action='store_true', help='Archive original bytes and migrate uniquely proven reviewed states.')
    args = parser.parse_args()
    root = args.root.resolve()
    if args.migration_report or args.migrate_rules:
        if args.output_dir:
            parser.error('migration cannot be combined with --output-dir')
        print(json.dumps(migrate_rules(root, args.source_id, apply=args.migrate_rules), ensure_ascii=False, indent=2))
    else:
        regenerate(root, output_dir=args.output_dir, source_id=args.source_id)


if __name__ == '__main__':
    main()
