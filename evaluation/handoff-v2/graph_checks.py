"""Read-only evaluation helpers. Never imported by the production parser.

Selectors locate actual emitted events by source anchors and public ports.
They do not add missing events, repair links, or substitute expected numbers.
"""
import re


def compact(text):
    return re.sub(r'[\s，,。．；;：:、]', '', text)


class Graph:
    def __init__(self, report):
        self.report = report
        self.values = {v['id']: v for v in report['value_instances']}
        self.events = {e['id']: e for e in report['events']}

    def unwrap(self, value):
        visited = set()
        while value in self.values and value not in visited:
            visited.add(value)
            event = self.events.get(self.values[value]['producer'], {})
            if event.get('kind') not in ('alias', 'load'):
                break
            reads = event.get('reads', {})
            if len(reads) != 1:
                break
            value = next(iter(reads.values()))
        return value

    def same(self, left, right):
        return left is not None and right is not None and self.unwrap(left) == self.unwrap(right)

    def at(self, quote=None, kind=None, doc=None, query=None):
        matches = []
        for event in self.events.values():
            if kind is not None and event['kind'] not in ({kind} if isinstance(kind, str) else kind):
                continue
            if query is not None and event['scope'].get('query') != query:
                continue
            spans = event['source_spans']
            if doc is not None:
                spans = [s for s in spans if s['doc_id'] == doc]
            if not spans:
                continue
            if quote and not any(compact(quote) in compact(s['quote']) or compact(s['quote']) in compact(quote) for s in spans):
                continue
            matches.append(event)
        if quote:
            exact = [e for e in matches if any(compact(s['quote']) == compact(quote)
                     for s in e['source_spans'] if doc is None or s['doc_id'] == doc)]
            if exact:
                return exact
        return matches

    def one(self, quote=None, kind=None, doc=None, query=None):
        candidates = self.at(quote, kind, doc, query)
        if len(candidates) != 1:
            raise AssertionError(f'Expected one {kind} event at {quote!r}; got {[e["id"] for e in candidates]}')
        return candidates[0]

    def output(self, event, port='result'):
        if port not in event['writes']:
            raise AssertionError(f'{event["id"]} has no {port} port: {event["writes"]}')
        return event['writes'][port]

    def producer(self, value, unalias=True):
        value = self.unwrap(value) if unalias else value
        return self.events[self.values[value]['producer']]

    def scalar(self, value):
        event = self.producer(value)
        if event['kind'] not in ('literal', 'parameter'):
            return None
        return event.get('attributes', {}).get('value', self.values[self.unwrap(value)].get('value'))

    def named(self, label, query='main', parameter=False):
        candidates = [v['id'] for v in self.values.values()
                      if label in v.get('labels', []) and v['scope'].get('query') == query
                      and (self.producer(v['id'])['kind'] == 'parameter') == parameter]
        if not candidates:
            raise AssertionError(f'Missing named value {query}:{label}, parameter={parameter}')
        return candidates[-1]

    def ancestors(self, value):
        result, pending = set(), [value]
        while pending:
            item = pending.pop()
            if item in result:
                continue
            result.add(item)
            if item in self.values:
                event = self.events.get(self.values[item]['producer'], {})
                pending.extend(v for v in event.get('reads', {}).values() if isinstance(v, str))
        return result

    def reads(self, event, *values):
        actual = list(event['reads'].values())
        return all(any(self.same(wanted, got) for got in actual) for wanted in values)

    def assert_port(self, value, producer, port):
        assert self.same(value, self.output(producer, port)), (value, producer['id'], port)


def span_audit(report):
    """Full source coverage comes from original documents, not recognized output."""
    docs = {d['doc_id']: d for d in report.get('documents', [])}
    errors = []
    for event in report['events']:
        if not event.get('source_spans'):
            errors.append({'event': event['id'], 'error': 'missing_source'})
        for span in event.get('source_spans', []):
            doc = docs.get(span['doc_id'])
            if not doc or doc['text'][span['start']:span['end']] != span['quote']:
                errors.append({'event': event['id'], 'error': 'invalid_span', 'span': span})
    return errors
