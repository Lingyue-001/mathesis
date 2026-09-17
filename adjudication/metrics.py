"""Decision accounting; scripted replay is never reported as human effort."""
from collections import Counter


def decision_metrics(session):
    decisions = session.get('decisions', [])
    actors = Counter(row.get('actor', {}).get('type', 'unknown') for row in decisions)
    actions = Counter(row.get('action', 'unknown') for row in decisions)
    human = [row for row in decisions if row.get('actor', {}).get('type') == 'human']
    return {'schema': 'AdjudicationMetrics', 'schema_version': '1.0',
            'decision_count': len(decisions), 'actions': dict(sorted(actions.items())),
            'actors': dict(sorted(actors.items())),
            'candidate_selection_count': actions['select_candidate'],
            'free_segmentation_count': actions['resegment'],
            'typed_manual_construction_count': actions['assemble_known_structure'],
            'binding_count': actions['bind_value'] + actions['bind_call'],
            'profile_or_background_count': actions['select_profile'] + actions['attach_context'],
            'schema_extension_request_count': sum(1 for row in decisions if row.get('action') == 'defer'
                                                  and row.get('payload', {}).get('schema_extension_required')),
            'human_active_seconds': None if not human else sum(row.get('active_seconds', 0) for row in human),
            'human_reading_seconds': None if not human else sum(row.get('reading_seconds', 0) for row in human)}
