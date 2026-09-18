"""Read-only comparison of anchored Pattern Lab steps with an existing graph.

This module belongs exclusively to evaluation. References/crosswalks are never
passed to a compiler. Matching is relational: one construction can implement
several manual steps, and one step can cite several disjoint source spans.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


def _hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _anchor_valid(anchor, document):
    a, b = anchor.get('start'), anchor.get('end')
    return (anchor.get('doc_id') == document['doc_id']
            and anchor.get('reading_id') == document['reading_id']
            and type(a) is int and type(b) is int
            and 0 <= a < b <= len(document['text'])
            and document['text'][a:b] == anchor.get('quote'))


def validate_reference(packet, reference):
    if reference.get('schema_version') == 'PatternStepReference/2':
        from .pattern_importer import PUNCTUATION
        documents = {d['doc_id']: d for d in packet['primary_documents'] + packet.get('context_documents', [])}
        old = reference['legacy_document']
        if reference.get('usage') != 'evaluation_only' or _hash(old['text']) != old['text_sha256']:
            raise ValueError('unsupported_reference_contract')
        for doc in reference['source_documents']:
            actual = documents.get(doc['doc_id'], {})
            if any(actual.get(k) != doc.get(k) for k in ('reading_id', 'text', 'text_sha256', 'source')):
                raise ValueError('reference_source_changed')
        compact = lambda t: ''.join(c for c in t if not c.isspace() and c not in PUNCTUATION)
        ids = set()
        for step in reference['steps']:
            if step['step_id'] in ids:
                raise ValueError('duplicate_reference_step')
            ids.add(step['step_id'])
            for field in ('legacy_anchors', 'source_anchors'):
                for anchor in step[field]:
                    doc = old if field == 'legacy_anchors' else documents.get(anchor['doc_id'])
                    if not doc or not _anchor_valid(anchor, doc) or anchor.get('offset_unit') != 'unicode_code_point':
                        raise ValueError('invalid_exact_anchor')
                if not step.get('issues') and (not step[field] or compact(''.join(a['quote'] for a in step[field])) != compact(step['legacy']['phrase'])):
                    raise ValueError('reference_phrase_anchor_mismatch')
        return
    raise ValueError('unsupported_reference_contract')


def _covers(spans, anchors, documents):
    """Require every character of every evidence span, not mere overlap."""
    valid = [s for s in spans if s.get('doc_id') in documents
             and _anchor_valid(s, documents[s['doc_id']])]
    return all(all(any(s['doc_id'] == a['doc_id'] and s['reading_id'] == a['reading_id']
                       and s['start'] <= i < s['end'] for s in valid)
                   for i in range(a['start'], a['end'])) for a in anchors)


def compare_reference(packet, graph, reference, crosswalk):
    """Consume an independently compiled report; never mutate any argument."""
    validate_reference(packet, reference)
    if crosswalk.get('schema_version') != 'PatternOperationCrosswalk/1' or crosswalk.get('usage') != 'evaluation_only':
        raise ValueError('unsupported_crosswalk_contract')
    documents = {d['doc_id']: d for d in packet['primary_documents'] + packet.get('context_documents', [])}
    machine_documents = {d['doc_id']: d for d in graph['documents']}
    if any(ident not in machine_documents or any(machine_documents[ident].get(k) != doc.get(k)
               for k in ('reading_id', 'text', 'text_sha256')) for ident, doc in documents.items()):
        raise ValueError('machine_source_mismatch')
    constructions = {c['node_id']: c for c in graph['construction_candidates'] if c.get('status') == 'selected'}
    events = {e['id']: e for e in graph['events']}
    values = {v['id']: v for v in graph['value_instances']}
    bindings, rows, groups = {}, [], {}
    for step in reference['steps']:
        row = {'step_id': step['step_id'], 'legacy': step['legacy'], 'source_anchors': step['source_anchors'],
               'legacy_anchors': step['legacy_anchors'], 'construction_ids': [], 'event_ids': [], 'checks': []}
        if step.get('issues'):
            row.update(status='reference_not_convertible', import_issues=step['issues'], details=step.get('details', []))
            rows.append(row)
            continue
        rule = crosswalk['operations'].get(step['legacy']['op'])
        if rule is None:
            row['status'] = 'crosswalk_missing'
            rows.append(row)
            continue
        expect = step['evaluation_expectation']
        unavailable = [e['reference'] for e in expect['reads'].values() if 'reference' in e and e['reference'] not in bindings]
        if unavailable:
            row.update(status='dependency_unavailable', unavailable_references=unavailable)
            rows.append(row)
            continue
        candidates = []
        for event in graph['events']:
            c = constructions.get(event.get('syntax_node_id'))
            if not c or not _covers(c['source_spans'], step['source_anchors'], documents):
                continue
            if not _covers(event['source_spans'], step['source_anchors'], documents):
                continue
            for alternative in rule['alternatives']:
                if (c['kind'] != alternative['construction_kind'] or event['kind'] != alternative['event_kind']
                        or any(s not in c['slots'] for s in alternative.get('required_slots', []))):
                    continue
                checks = []
                for role, expected in expect['reads'].items():
                    port = alternative['read_ports'].get(role)
                    vid = event['reads'].get(port)
                    value = values.get(vid, {})
                    producer = events.get(value.get('producer'), {})
                    if 'reference' in expected:
                        ok = expected['reference'] in bindings and vid == bindings[expected['reference']]
                    elif 'label' in expected:
                        ok = expected['label'] in value.get('labels', [])
                    else:
                        ok = producer.get('kind') == 'literal' and producer.get('attributes', {}).get('value') == expected['literal']
                    checks.append({'role': role, 'port': port, 'expected': expected, 'value_id': vid,
                                   'producer': producer.get('id'), 'producer_port': next((p for p, v in producer.get('writes', {}).items() if v == vid), None),
                                   'pass': ok and vid in producer.get('writes', {}).values()})
                for key, expected in expect.get('attributes', {}).items():
                    checks.append({'attribute': key, 'expected': expected, 'actual': event['attributes'].get(key),
                                   'pass': event['attributes'].get(key) == expected})
                for port in expect['outputs']:
                    vid = event['writes'].get(port)
                    checks.append({'output_port': port, 'value_id': vid,
                                   'pass': vid in values and values[vid].get('producer') == event['id']})
                candidates.append((c, event, checks))
        passing = {e['id']: (c, e, checks) for c, e, checks in candidates if all(x['pass'] for x in checks)}
        all_events = {e['id']: (c, e, checks) for c, e, checks in candidates}
        if len(passing) == 1:
            c, e, checks = next(iter(passing.values()))
            row.update(status='match', construction_ids=[c['node_id']], event_ids=[e['id']], checks=checks,
                       machine_kind=c['kind'], event_kind=e['kind'], production_id=c['production_id'],
                       outputs={p: e['writes'][p] for p in expect['outputs']})
            for port, name in expect['outputs'].items():
                bindings[name] = e['writes'][port]
            groups.setdefault(c['node_id'], []).append(step['step_id'])
        else:
            row['status'] = 'ambiguous' if len(passing) > 1 else 'mismatch' if candidates else 'missing_machine_semantics'
            row['construction_ids'] = sorted({c['node_id'] for c, _, _ in candidates})
            row['event_ids'] = sorted(all_events)
            row['checks'] = [{'event_id': e['id'], 'checks': checks} for _, e, checks in candidates]
        rows.append(row)
    return {'schema_version': 'PatternReferenceComparison/1', 'usage': 'evaluation_only',
            'reference_id': reference['reference_id'], 'rows': rows, 'construction_groups': groups,
            'matched_steps': sum(r['status'] == 'match' for r in rows), 'total_steps': len(rows),
            'machine_unresolved': graph.get('unresolved', []), 'machine_diagnostics': graph.get('diagnostics', []),
            'machine_program_diagnostics': graph.get('program', {}).get('diagnostics', []),
            'machine_link_diagnostics': graph.get('program', {}).get('linked', {}).get('diagnostics', []),
            'machine_unparsed_spans': graph.get('coverage', {}).get('unparsed_spans', []),
            'input_hashes': {name: _hash(json.dumps(value, ensure_ascii=False, sort_keys=True))
                             for name, value in [('packet', packet), ('graph', graph), ('reference', reference), ('crosswalk', crosswalk)]},
            'graph_closure': 'not_assessed_by_reference_comparison',
            'limitation': 'Agreement with existing manual steps is not graph closure, scholarly approval or independent historical validation.'}


def render_markdown(result):
    lines = [f"# {result['reference_id']} — reference 与 machine 对照", '',
             '仅用于 evaluation。原人工 steps 原样保留；reference 由确定性 Python importer 机械生成。', '',
             '| 人工步骤 | 原文／corpus 字符区间 | 旧 operation | machine construction → event | 结果 |',
             '|---|---|---|---|---|']
    for r in result['rows']:
        spans = '；'.join(f"{a['quote']} [{a['start']},{a['end']})" for a in r['source_anchors'])
        machine = f"{r.get('machine_kind', '—')} / {','.join(r['construction_ids'])} → {r.get('event_kind', '—')} / {','.join(r['event_ids'])}"
        lines.append(f"| {r['step_id']} | {spans} | {r['legacy']['op']} | {machine} | {r['status']} |")
    lines += ['', '| 步骤 | 原人工 input / parameter → output | 实际机器输入（producer.port）→ 输出 |',
              '|---|---|---|']
    for row in result['rows']:
        old = row['legacy']
        expected = f"{old['input']} / {old['parameter'] or '—'} → {old['output']}"
        inputs = [f"{c['role']}={c['value_id']} ({c['producer']}.{c['producer_port']})"
                  for c in row['checks'] if 'role' in c]
        outputs = [f"{port}={value}" for port, value in row.get('outputs', {}).items()]
        lines.append(f"| {row['step_id']} | {expected} | {'; '.join(inputs)} → {'; '.join(outputs)} |")
    lines += ['', f"语义步骤对照：{result['matched_steps']}/{result['total_steps']}。这不是 parser 准确率或图闭合率。",
              '', '## 粒度与证据', '']
    for construction, steps in result['construction_groups'].items():
        if len(steps) > 1:
            lines.append(f"- 一个 machine construction `{construction}` 对应多个 manual semantic steps：{', '.join(steps)}。")
    for row in result['rows']:
        if len(row['source_anchors']) > 1:
            lines.append(f"- {row['step_id']} 使用 {len(row['source_anchors'])} 个 exact source spans：" + '；'.join(a['quote'] for a in row['source_anchors']) + '。')
    lines += [
              '- 逐步检查输入引用、producer/output port、literal、商／余数及命名／判断属性；文字重叠本身不算 match。',
              '- 两份 reading、原始人工字段、逐字符映射和导入 provenance 见 proc-3.5.json；operation 映射见 operation-crosswalk.json。',
              '', '## 机器仍然存在的缺口', '', '```json',
              json.dumps({k: result[k] for k in ('machine_unresolved', 'machine_diagnostics', 'machine_program_diagnostics', 'machine_link_diagnostics', 'machine_unparsed_spans')}, ensure_ascii=False, indent=2),
              '```', '', 'Reference 不修改上述缺口，不判定 graph closure，也不传给 parser。', '',
              '复现 Proc.3.5：`python -X utf8 -m evaluation.pattern_reference --output .cache/pattern-reference`。',
              '', '## 输入身份（JSON 按键排序、UTF-8 的 SHA-256）', '',
              '```json', json.dumps(result['input_hashes'], indent=2), '```', '']
    return '\n'.join(lines)


def run_batch(root):
    """Finish both machine runs before opening ANY annotation/crosswalk asset."""
    from source_adapters.corpus import build_source_packet
    from analysis_parser.pipeline import parse_packet
    from .pattern_importer import import_annotations, source_document
    root = Path(root)
    phases = []
    packet = build_source_packet(root, 'sifen-3-5')['source_packet']
    graph = parse_packet(packet)
    phases.append('compiled_registered_local_packet')
    raw = (root / 'calendars-四分历.md').read_bytes()
    text = raw.decode('utf-8')
    documents = []
    for match in re.finditer(r'^(\d+)[ \t]+([^\r\n]+)', text, re.MULTILINE):
        doc = source_document('sifen:' + match[1], match[2])
        doc['source'] = {'path': 'calendars-四分历.md', 'section': int(match[1]),
                         'start': match.start(2), 'end': match.end(2), 'offset_unit': 'unicode_code_point',
                         'corpus_sha256': hashlib.sha256(raw).hexdigest()}
        documents.append(doc)
    corpus = {'schema_version': '3.0', 'packet_id': 'evaluation:canonical-sifen-all-sections',
              'provided_scope': {'tradition': 'Han_Si_fen_li'}, 'primary_documents': documents, 'context_documents': []}
    machine = parse_packet(corpus)
    phases.append('compiled_full_canonical_corpus')
    assets = root / 'evaluation/pattern-reference'
    frozen = json.loads((assets / 'frozen-inputs.json').read_text(encoding='utf-8'))
    for path, expected in frozen['sha256'].items():
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != expected:
            raise ValueError('frozen_input_changed: ' + path)
    crosswalk = json.loads((assets / 'operation-crosswalk.json').read_text(encoding='utf-8'))
    annotations = json.loads((assets / 'ch3-chunk-breakdown.json').read_text(encoding='utf-8'))
    sources = json.loads((assets / 'source-chunks.json').read_text(encoding='utf-8'))
    phases.append('read_full_annotations_and_fixed_crosswalk')
    imported = import_annotations(annotations, sources, corpus, crosswalk)
    # Local baseline is selected by registered source/procedure metadata, never
    # an authored set of expectations. Both import calls consume the full JSON.
    local = import_annotations(annotations, sources, packet, crosswalk)
    target = next(c['procedure_reference'] for c in local['chunks']
                  if c['procedure_reference'] and 'Proc. 3.5' in c['procedure_reference']['procedure_ids'])
    phases.append('deterministic_import')
    comparison = compare_reference(packet, graph, target, crosswalk)
    batch = [compare_reference(corpus, machine, r['procedure_reference'], crosswalk)
             for r in imported['chunks'] if r['procedure_reference']]
    phases.append('evaluation_only_comparison')
    summary = {'schema_version': 'PatternBatchEvaluation/1', 'actor': 'deterministic_python_software_evaluation',
               'pipeline_order': phases, 'frozen_inputs': frozen,
               'annotation_chunks': len(annotations),
               'terms': sum(len(r.get('terms', [])) for r in annotations),
               'relations': sum(len(r.get('relations', [])) for r in annotations),
               'procedure_chunks': len(batch),
               'lexical_reference_statuses': dict(sorted(Counter(t['status'] for c in imported['chunks'] for t in c['lexical_semantic_reference']).items())),
               'relation_target_statuses': dict(sorted(Counter(t['target_status'] for c in imported['chunks'] for t in c['relation_reference']).items())),
               'import_issues': dict(sorted(Counter(i for c in imported['chunks'] if c['procedure_reference'] for s in c['procedure_reference']['steps'] for i in s['issues']).items())),
               'crosswalk_missing_operations': sorted({s['legacy']['op'] for c in imported['chunks'] if c['procedure_reference'] for s in c['procedure_reference']['steps'] if 'crosswalk_missing' in s['issues']}),
               'local_proc35': {'matched': comparison['matched_steps'], 'total': comparison['total_steps']},
               'batch': [{'reference_id': b['reference_id'], 'matched': b['matched_steps'], 'total': b['total_steps'],
                          'statuses': dict(sorted(Counter(r['status'] for r in b['rows']).items()))} for b in batch]}
    return imported, target, comparison, batch, summary


def render_batch(summary, results):
    lines = ['# Deterministic Pattern Lab reference import — frozen parser batch', '',
             'Actor: deterministic Python software evaluation。没有新人工判断；没有修改 parser 或固定 crosswalk。', '',
             f"完整导入：{summary['annotation_chunks']} chunks / {summary['terms']} terms / {summary['relations']} relations。",
             f"Proc.3.5 原局部 packet：{summary['local_proc35']['matched']}/{summary['local_proc35']['total']}。", '',
             '批量输入是独立于 annotation 的 canonical 四分历全部编号章节；先编译，再读取 annotation。与局部 packet 的输入范围不同，结果分别报告。', '',
             '| Chunk | 原始步数 | 可转换步骤 | 匹配 | 结果分布 |', '|---|---|---|---|---|']
    for b in summary['batch']:
        convertible = b['total'] - b['statuses'].get('reference_not_convertible', 0)
        lines.append(f"| {b['reference_id']} | {b['total']} | {convertible} | {b['matched']} | {json.dumps(b['statuses'], ensure_ascii=False)} |")
    lines += ['', '## 导入状态（不算 parser false negative）', '',
              '```json', json.dumps({k: summary[k] for k in ('lexical_reference_statuses', 'relation_target_statuses', 'import_issues', 'crosswalk_missing_operations')}, ensure_ascii=False, indent=2), '```', '',
              '所有 relations 单独保留为 not_current_parser_target。词项/参数/数量单独生成 lexical/semantic reference。',
              'reference_not_convertible、dependency_unavailable 不得与已可评估步骤的机器缺失混算。匹配不代表历史真值、单位/尺度验证或 graph closure。', '',
              '## 每步结果', '', '| Chunk / step | 原 phrase | 原 operation | 状态 | 导入问题／细节 |', '|---|---|---|---|---|']
    for result in results:
        for row in result['rows']:
            details = row.get('import_issues', []) + row.get('details', []) + row.get('unavailable_references', [])
            lines.append(f"| {result['reference_id']} / {row['step_id']} | {row['legacy']['phrase']} | {row['legacy']['op']} | {row['status']} | {'; '.join(details)} |")
    lines += ['', '复现：`python -X utf8 -m evaluation.pattern_reference --output .cache/pattern-reference-run`。',
              '完整原始对象、exact anchors、小语法 AST、每步 checks、未决诊断及 SHA manifest 均在该输出目录；重复运行按文件逐字节比较。', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    root = Path(__file__).resolve().parents[1]
    args = parser.parse_args()
    imported, reference, result, batch, summary = run_batch(root)
    args.output.mkdir(parents=True, exist_ok=True)
    output = {'imported.json': imported, 'proc-3.5.json': reference, 'comparison.json': result, 'batch.json': batch, 'summary.json': summary}
    for name, value in output.items():
        (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    (args.output / 'comparison.md').write_text(render_markdown(result), encoding='utf-8', newline='\n')
    (args.output / 'batch.md').write_text(render_batch(summary, batch), encoding='utf-8', newline='\n')
    names = sorted([*output, 'comparison.md', 'batch.md'])
    hashes = {n: hashlib.sha256((args.output / n).read_bytes()).hexdigest() for n in names}
    (args.output / 'sha256.json').write_text(json.dumps(hashes, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'local': summary['local_proc35'], 'batch': summary['batch'], 'import_issues': summary['import_issues']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
