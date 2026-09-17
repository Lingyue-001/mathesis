"""Research-facing reconstruction trace derived from the compiled typed graph."""

def _comparison(computed, reference):
    if computed is None or reference is None:
        return {'status': 'unavailable'}
    return {'status': 'exact' if computed == reference else 'mismatch'}

def build_reconstruction_trace(graph, source_attested_values=None, scholarly_reconstructed_values=None, computed_values=None):
    source_attested_values = source_attested_values or {}
    scholarly_reconstructed_values = scholarly_reconstructed_values or {}
    computed_values = computed_values or {}
    values = {row['id']: row for row in graph.get('value_instances', [])}
    consumers = {}
    for event in graph.get('events', []):
        for slot, value_id in event.get('reads', {}).items():
            consumers.setdefault(value_id, []).append({'event_id': event['id'], 'operation': event['kind'], 'slot': slot})
    steps = []
    for event in graph.get('events', []):
        outputs = []
        for port, value_id in event.get('writes', {}).items():
            value = values.get(value_id, {})
            outputs.append({'value_id': value_id, 'port': port,
                            'unit': value.get('unit'), 'scale': value.get('scale'),
                            'representation': value.get('representation'),
                            'producer': {'event_id': event['id'], 'output_port': port},
                            'downstream_consumers': consumers.get(value_id, [])})
        operands = []
        for slot, value_id in event.get('reads', {}).items():
            value = values.get(value_id, {})
            operands.append({'slot': slot, 'value_id': value_id,
                             'producer': {'event_id': value.get('producer'), 'output_port': value.get('output_port')},
                             'unit': value.get('unit'), 'scale': value.get('scale'),
                             'representation': value.get('representation')})
        attested = source_attested_values.get(event['id'])
        reconstructed = scholarly_reconstructed_values.get(event['id'])
        computed = next((computed_values.get(row['value_id']) for row in outputs if row['value_id'] in computed_values), None)
        steps.append({'step_id': event['id'], 'source_spans': event.get('source_spans', []),
                      'normalized_operation': event['kind'], 'formula': event.get('attributes', {}).get('formula'),
                      'operands': operands, 'unit_scale_representation': [{'port': row['port'], 'unit': row['unit'], 'scale': row['scale'], 'representation': row['representation']} for row in outputs],
                      'derived_outputs': outputs, 'source_attested_value': attested,
                      'scholarly_reconstructed_value': reconstructed, 'computed_value': computed,
                      'comparisons': {'computed_vs_source': _comparison(computed, attested),
                                      'computed_vs_scholar': _comparison(computed, reconstructed)}})
    return {'schema': 'StepReconstructionTrace', 'schema_version': '1.0', 'steps': steps}
