#!/usr/bin/env python3
"""Rebuild any registered corpus workspace (historical command name retained).

This command reads only the registered corpus and explicit review overrides.
It does not import the parser, evaluator, Pattern Lab, or adjudication code.
"""
import argparse
from pathlib import Path
import sys


REPOSITORY = Path(__file__).resolve().parents[2]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from source_adapters.corpus_review import regenerate


def main():
    parser = argparse.ArgumentParser(description='Rebuild a registered corpus review workspace.')
    parser.add_argument('--root', type=Path, default=REPOSITORY)
    parser.add_argument('--source-id', default='sifen')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    regenerate(root, output_dir=args.output_dir, source_id=args.source_id)


if __name__ == '__main__':
    main()
