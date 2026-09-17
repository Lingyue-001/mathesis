"""Source-occurrence and recursive producer/port contracts for civil task cards.

This is a grader, never a graph constructor. Policies describe relations from
the curated source cards; value IDs and parser labels alone are not evidence.
Composite reference spans admit local constituent spans with exact identities.
"""
import hashlib
import itertools


def subset(actual, expected):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and subset(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(subset(a, e) for a, e in zip(actual, expected))
    return actual == expected


class Graph:
    def __init__(self, packet, report):
        self.report = report
        self.packet = packet
        self.values = {v['id']: v for v in report.get('value_instances', report.get('values', []))}
        self.events = {e['id']: e for e in report.get('events', [])}
        self.docs = {(d['doc_id'], d.get('reading_id', d['doc_id'] + '.declared')): d for category in ('primary_documents', 'context_documents')
                     for d in packet.get(category, [])}
        self.hashes = {key: hashlib.sha256(d['text'].encode()).hexdigest() for key, d in self.docs.items()}
        self.source_errors = []
        for e in self.events.values():
            for span in e.get('source_spans', []):
                if not self.valid_span(span):
                    self.source_errors.append({'event_id': e['id'], 'span': span})

    def valid_span(self, span):
        key = span.get('doc_id'), span.get('reading_id'); doc = self.docs.get(key)
        a, b = span.get('start'), span.get('end')
        return bool(doc and isinstance(a, int) and isinstance(b, int)
                    and 0 <= a < b <= len(doc['text']) and doc['text'][a:b] == span.get('quote')
                    and span.get('text_sha256', span.get('reading_hash', self.hashes[key])) == self.hashes[key])

    def at(self, event, anchor):
        if not self.valid_span(anchor):
            raise ValueError('Invalid reference anchor: ' + repr(anchor))
        return any(self.valid_span(s) and s['doc_id'] == anchor['doc_id']
                   and s['reading_id'] == anchor['reading_id']
                   and anchor['start'] <= s['start'] < s['end'] <= anchor['end']
                   for s in event.get('source_spans', []))

    def root(self, vid):
        seen = set()
        while vid in self.values and vid not in seen:
            seen.add(vid); value = self.values[vid]; event = self.events.get(value.get('producer'), {})
            if event.get('writes', {}).get(value.get('output_port')) != vid:
                return None
            if event.get('kind') not in ('alias', 'load') or value.get('output_port') != 'result':
                return vid
            vid = event.get('reads', {}).get('value')
        return None

    def value(self, vid, selector, active=None):
        active = active or set(); root = self.root(vid)
        if root is None or root in active or not isinstance(selector, dict):
            return False
        value = self.values[root]; event = self.events[value['producer']]
        attrs = event.get('attributes', {})
        observed = [self.values.get(vid, {}), value]
        if 'export' in selector:
            task, port = selector['export']
            observed.append(self.values.get(self.report.get('task_exports', {}).get(task, {}).get(port), {}))
        for actual in observed:
            for field in ('unit', 'quantity_kind', 'time_frame'):
                if field in selector and (actual is value or field in actual) and actual.get(field) != selector[field]:
                    return False
            if 'denominator' in selector:
                scale = actual.get('scale', {})
                representation = actual.get('representation', {})
                ids = [x for x in (scale.get('denominator') if isinstance(scale, dict) else None,
                                  representation.get('denominator_id')) if x]
                if not ids or any(not self.value(x, selector['denominator'], active | {root}) for x in ids):
                    return False
                if isinstance(scale, dict) and 'value' in scale:
                    den = self.root(ids[0]); producer = self.events[self.values[den]['producer']]
                    if scale['value'] != producer.get('attributes', {}).get('value'):
                        return False
        if selector.get('anchor') and not self.at(event, selector['anchor']):
            return False
        if 'one_of' in selector:
            return any(self.value(root, option, active) for option in selector['one_of'])
        if 'export' in selector:
            task, port = selector['export']
            return root == self.root(self.report.get('task_exports', {}).get(task, {}).get(port))
        if 'input' in selector:
            return event.get('kind') == 'input' and attrs.get('name') == selector['input']
        if 'literal' in selector:
            return (event.get('kind') == 'literal' and type(attrs.get('value')) is type(selector['literal'])
                    and attrs.get('value') == selector['literal'])
        if 'parameter' in selector:
            names = value.get('labels', []) + [attrs.get('name'), value.get('source_label')]
            return (event.get('kind') == 'parameter' and selector['parameter'] in names
                    and ('value' not in selector or attrs.get('value') == selector['value']))
        origin = selector.get('origin')
        if origin is not None:
            if value.get('output_port') != origin.get('port', 'result'):
                return False
            if origin.get('anchor') and not self.at(event, origin['anchor']):
                return False
            ok, _ = self.event(event, {k: v for k, v in origin.items() if k not in ('port', 'anchor')}, active | {root})
            return ok
        return False

    def event(self, event, predicate, active=None):
        checks = []
        kinds = predicate.get('kind')
        checks.append(('source_action', event.get('kind') in kinds if isinstance(kinds, list) else event.get('kind') == kinds))
        for direction in ('reads', 'writes'):
            for port, selector in predicate.get(direction, {}).items():
                vid = event.get(direction, {}).get(port)
                valid = self.value(vid, selector, active)
                if direction == 'writes':
                    v = self.values.get(vid, {})
                    valid = valid and v.get('producer') == event['id'] and v.get('output_port') == port
                checks.append((direction + '.' + port, valid))
            if predicate.get('exact_' + direction):
                checks.append((direction + '.port_set', set(event.get(direction, {})) == set(predicate.get(direction, {}))))
        for field in ('scope', 'attributes', 'control', 'method_binding', 'quantity'):
            if field in predicate:
                checks.append((field, subset(event.get(field, event.get('attributes', {}).get(field)), predicate[field])))
        attrs = event.get('attributes', {})
        if 'control' in predicate and 'control' in event and 'control' in attrs:
            checks.append(('control.execution_identity', event['control'] == attrs['control']))
        if predicate.get('branch_contract') == 'three_concordances':
            choices = attrs.get('choices', [])
            checks.append(('branch.cases', len(choices) == 3 and [c.get('label') for c in choices] == ['天統', '地統', '人統']))
            checks.append(('branch.conditions', len(choices) == 3 and all(
                c.get('index') == i and c.get('condition') == {'operator': 'ge_lt', 'lower': 0, 'upper': 'divisor'}
                and c.get('local_port') == 'local' + str(i) and c.get('head_port') == 'head' + str(i)
                for i, c in enumerate(choices))))
        if predicate.get('table_contract') == 'full_source_table':
            table = attrs.get('table', {})
            supplied = [t for t in self.packet.get('context_tables', []) if t.get('table_id') == table.get('table_id')]
            checks.append(('table.source_identity', len(supplied) == 1 and table == supplied[0]))
            columns = table.get('columns', [])
            checks.append(('table.indices', '蔀首日' in columns and attrs.get('day_column') == columns.index('蔀首日')
                           and attrs.get('row_base') == 1 and attrs.get('column_base') == 0))
        if predicate.get('method_contract'):
            definitions = [m for m in self.report.get('method_library', []) if m.get('id') == attrs.get('target')]
            method = definitions[0] if len(definitions) == 1 else {}
            body = method.get('body', [])
            binding = event.get('method_binding', {})
            checks.append(('method.target', bool(method) and binding.get('definition_id') == method.get('id')))
            checks.append(('method.body', bool(body) and body == attrs.get('body') and method.get('returns') == attrs.get('formal_returns')))
            checks.append(('method.actuals', bool(binding) and binding.get('actuals') == event.get('reads')))
            signature = method.get('formal_inputs', {})
            checks.append(('method.signature', subset(signature, {'offset': {'unit': 'day'}, 'origin': {'unit': 'day_index'}, 'cycle': {'unit': 'integer'}})))
            checks.append(('method.bound_signature', binding.get('formal_inputs') == signature))
            valid_body = (len(body) == 2 and body[0].get('kind') == 'cycle_reduce' and body[1].get('kind') == 'count'
                          and body[0].get('reads') == {'dividend': '$offset', 'divisor': '$cycle'}
                          and body[1].get('reads') == {'offset': body[0].get('writes', {}).get('remainder'), 'origin': '$origin', 'cycle': '$cycle'})
            checks.append(('method.semantic_body', valid_body))
            anchor = predicate['method_contract'].get('definition_anchor')
            checks.append(('method.definition_source', bool(method and anchor) and self.at(method, anchor)))
        if predicate.get('rate_contract'):
            contract = predicate['rate_contract']; transition = attrs.get('quantity_transition', {}); rate = transition.get('rate', {})
            checks.append(('rate.resolved', transition.get('status') == 'resolved' and transition.get('transition') == 'rate_conversion'))
            checks.append(('rate.units', rate.get('from_unit') == contract['from_unit'] and rate.get('to_unit') == contract['to_unit']))
            checks.append(('rate.factor', self.value(rate.get('numerator_parameter'), contract['factor'])))
            checks.append(('rate.denominator', self.value(rate.get('denominator_parameter'), contract['denominator'])))
            checks.append(('rate.operand', self.value(transition.get('operand'), contract['operand'])))
            source = self.events.get(transition.get('source_operation'), {})
            numerator = self.root(event.get('reads', {}).get('dividend'))
            checks.append(('rate.source_operation', bool(numerator) and self.values[numerator]['producer'] == source.get('id') and source.get('kind') == 'multiply'))
            checks.append(('rate.scope_evidence', bool(rate.get('basis')) and event.get('scope', {}).get('tradition') in rate.get('traditions', [])
                           and event.get('scope', {}).get('task') in rate.get('tasks', []) and transition.get('scope') == event.get('scope')))
            for name, parameter in (('numerator', 'numerator_parameter'), ('denominator', 'denominator_parameter')):
                vid = self.root(rate.get(parameter)); producer = self.events.get(self.values.get(vid, {}).get('producer'), {})
                checks.append(('rate.' + name + '_value', bool(producer) and rate.get(name) == producer.get('attributes', {}).get('value')))
        return all(ok for _, ok in checks), checks


def evaluate_cards(packet, report, cards, policy):
    graph = Graph(packet, report); supported = set(policy['supported_actions'])
    totals = {'TP': 0, 'FP': 0, 'FN': 0}; output = []; unsupported = False
    for card in cards:
        rows = []
        for obligation in card['obligations']:
            oid = obligation['id']; rule = policy.get('obligations', {}).get(oid)
            row = {'id': oid, 'anchor': obligation['anchor'], 'matched_event_ids': []}
            if not rule or not rule.get('events'):
                row.update(status='evaluator_unsupported', reason='No frozen semantic relation policy', relations=None)
                unsupported = True; rows.append(row); continue
            predicates = rule['events']
            candidates = [e for e in graph.events.values() if any(graph.at(e, pred.get('anchor', obligation['anchor'])) for pred in predicates)]
            unknown = [e for e in candidates if e['kind'] not in supported]
            known = [e for e in candidates if e['kind'] in supported]
            scored = []
            for chosen in itertools.permutations(known, len(predicates)):
                results = []
                for e, p in zip(chosen, predicates):
                    ok, tests = graph.event(e, p)
                    tests.append(('source.occurrence', graph.at(e, p.get('anchor', obligation['anchor']))))
                    results.append((ok, tests))
                checks = [(e['id'], name, ok) for e, (_, tests) in zip(chosen, results) for name, ok in tests]
                for exported in rule.get('exports', []):
                    task, port = exported['path']
                    vid = report.get('task_exports', {}).get(task, {}).get(port)
                    checks.append(('export', task + '.' + port, graph.value(vid, exported['value'])))
                failures = sum(not ok for _, _, ok in checks)
                scored.append((failures, tuple(e['id'] for e in chosen), checks))
            best = min(scored, default=None, key=lambda x: (x[0], x[1]))
            if unknown and (best is None or best[0]):
                row.update(status='evaluator_unsupported', actual_kinds=sorted({e['kind'] for e in unknown}), relations=None)
                unsupported = True
            elif best is None:
                row.update(status='parser_error', reason='Required source-linked realization missing',
                           relations={'TP': 0, 'FP': 0, 'FN': len(predicates)})
            else:
                failures, ids, checks = best
                row.update(status='pass' if failures == 0 else 'parser_error', matched_event_ids=list(ids),
                           checks=[{'event_id': eid, 'relation': name, 'passed': ok} for eid, name, ok in checks],
                           relations={'TP': len(checks) - failures, 'FP': failures, 'FN': failures})
            if row.get('relations'):
                for name in totals:
                    totals[name] += row['relations'][name]
            rows.append(row)
        output.append({'card_id': card['card_id'], 'obligations': rows,
                       'passed': all(r['status'] == 'pass' for r in rows)})
    p, r = totals['TP'] + totals['FP'], totals['TP'] + totals['FN']
    totals['precision'] = totals['TP'] / p if p else None
    totals['recall'] = totals['TP'] / r if r else None
    totals['F1'] = 2 * totals['TP'] / (p + r) if p + r else None
    return {'cards': output, 'relations': totals, 'source_errors': graph.source_errors,
            'all_obligations_passed': None if unsupported else bool(output) and not graph.source_errors and all(c['passed'] for c in output),
            'coverage_domain': 'Listed semantic obligations only; full source token coverage reported separately',
            'annotation_policy_version': policy.get('version')}
