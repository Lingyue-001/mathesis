"""Pure typed predicates shared by lowering and its provenance sidecar."""
from copy import deepcopy


def ordinal_to_elapsed(coordinate, decrement):
    """The existing source ordinal transition; no source vocabulary is inspected."""
    if (coordinate.get('coordinate_kind') != 'ordinal' or coordinate.get('index_base') != 1
            or decrement != 1 or not coordinate.get('step_unit') or coordinate.get('unresolved_facets')):
        return None
    result = {k: deepcopy(coordinate[k]) for k in ('step_unit', 'reference_origin', 'counting_boundary') if k in coordinate}
    return dict(result, unit=coordinate['step_unit'], coordinate_kind='elapsed', index_base=0)
