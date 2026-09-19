"""Canonical backend terminology. Describes codes; never authorizes or executes them.

Grammar aliases come from the formal grammar table, not source-code scraping.
Operation signatures remain in their existing validation owner. Adding a code
requires authored language here; a missing entry is an error, never a fallback.
"""
from copy import deepcopy
from .construction_ir import GRAMMAR

VERSION = '1.0'
REGISTRY = {}

# The second reading is concise, authored English for researcher-facing use.
# It is separate from the Chinese label and the longer Chinese methodology.
# Inspector presentation does not select it yet; keeping the language here
# means that later presentation code reads one canonical vocabulary.
_DEFINITION_EN = {}
INSPECTOR_DEFAULT_CATEGORIES = frozenset({'operation', 'construction', 'syntax', 'frame', 'cause'})
TECHNICAL_ONLY_ENGLISH = frozenset({
    *{('profile', code) for code in (
        'ST_elapsed', 'SF_Liu_inclusive', 'SF_completed_four', 'instant_lunation', 'civil_whole_day',
        'ST_intercalation_Cullen_Liu_GT', 'ST_intercalation_GE_contrast',
        'C2017_ST_Jupiter_parameter_roles_v1', 'C2017_ST_local_year_count_v1',
        'C2017_ST_Jupiter_station_rate_v1', 'C2017_ST_Section_four_Rules_conditional_v1',
        'C2017_ST_origin_month_day_frame_v1', 'C2017_ST_concordance_midnight_frame_v1',
    )},
    ('action_variant', 'defer:unresolved'), ('action_variant', 'defer:schema_extension_required'),
})

# Short authored English for ordinary researcher-facing UI.  These are never
# derived from backend codes.  Source-text targets remain source text elsewhere.
_LABEL_EN = {
    ('operation', 'input'): 'Input quantity', ('operation', 'literal'): 'Literal value',
    ('operation', 'parameter'): 'Parameter', ('operation', 'load'): 'Load quantity',
    ('operation', 'multiply'): 'Multiply', ('operation', 'add'): 'Add',
    ('operation', 'subtract'): 'Subtract', ('operation', 'divmod'): 'Divide with remainder',
    ('operation', 'cycle_reduce'): 'Reduce by cycle', ('operation', 'alias'): 'Name quantity',
    ('operation', 'threshold'): 'Test threshold', ('operation', 'count'): 'Count from origin',
    ('operation', 'year_scan'): 'Step through years', ('operation', 'interval_scale'): 'Scale interval',
    ('operation', 'method_call'): 'Call method', ('operation', 'select'): 'Select result',
    ('operation', 'lookup'): 'Look up value', ('operation', 'rescale'): 'Rescale quantity',
    ('operation', 'fraction'): 'Form fraction', ('operation', 'convert'): 'Convert units',
    ('operation', 'epoch_frame'): 'Set epoch frame', ('operation', 'repeat'): 'Repeat calculation',
    ('operation', 'cycle_lift'): 'Lift cycle position', ('operation', 'event_sequence'): 'Generate event sequence',
    ('operation', 'boundary_call'): 'Apply boundary rule', ('operation', 'framed_origin'): 'Set framed origin',
    ('operation', 'initial_instant'): 'Set initial instant', ('operation', 'judgment'): 'Record judgment',

    ('construction', 'task_marker'): 'Procedure heading', ('construction', 'query_marker'): 'Calculation-stage heading',
    ('construction', 'update_count'): 'Update and count', ('construction', 'numeral_predicate'): 'Multiply by numeral',
    ('construction', 'denominator_declaration'): 'Declare denominator', ('construction', 'multiply'): 'Multiply',
    ('construction', 'multiply_focus'): 'Multiply current quantity', ('construction', 'subtract'): 'Subtract',
    ('construction', 'update'): 'Update quantity', ('construction', 'pair_increment'): 'Add named increment',
    ('construction', 'load'): 'Load quantity', ('construction', 'divide'): 'Divide with remainder',
    ('construction', 'cycle_divide'): 'Reduce by cycle', ('construction', 'divide_by'): 'Divide by named divisor',
    ('construction', 'pending_cycle'): 'Incomplete cycle reduction', ('construction', 'loop_threshold'): 'Loop threshold',
    ('construction', 'remainder_name'): 'Name remainder', ('construction', 'name'): 'Name quantity',
    ('construction', 'receiver_add'): 'Add to receiver', ('construction', 'count_origin'): 'Set counting origin',
    ('construction', 'count_command'): 'Count from named origin', ('construction', 'count_remainder'): 'Count from remainder',
    ('construction', 'threshold'): 'Threshold condition', ('construction', 'add'): 'Add quantity',
    ('construction', 'recur_increment'): 'Add recurring increment', ('construction', 'double_interval'): 'Double interval',
    ('construction', 'mixed_compact'): 'Mixed whole-and-fraction value', ('construction', 'declaration'): 'Declare value',
    ('construction', 'parameter_alias'): 'Alias parameter', ('construction', 'mixed_duration'): 'Mixed duration',
    ('construction', 'reuse_operation'): 'Repeat previous operation', ('construction', 'epoch_load'): 'Load elapsed epoch years',
    ('construction', 'method_value_reference'): 'Apply referenced method', ('construction', 'scalar_value'): 'Declare scalar',
    ('construction', 'scalar_name'): 'Name scalar', ('construction', 'schedule_row'): 'Schedule-table row',
    ('construction', 'scan_length'): 'Repeated subtraction length', ('construction', 'epoch_divide'): 'Divide epoch accumulation',
    ('construction', 'entry_cycle'): 'Enter cycle', ('construction', 'entry_remainder_divide'): 'Divide entry remainder',
    ('construction', 'concordance_case'): 'Concordance branch', ('construction', 'conditional_count'): 'Conditional count',
    ('construction', 'method_reference'): 'Use previous method', ('construction', 'use_denominator'): 'Reuse denominator',
    ('construction', 'complete_cycle'): 'Complete cycle reduction', ('construction', 'judgment'): 'Judgment statement',
    ('construction', 'annotation'): 'Explanatory text', ('construction', 'boundary'): 'Event-boundary statement',
    ('construction', 'concordance_pending'): 'Incomplete concordance step', ('construction', 'concordance_remainder'): 'Concordance remainder',
    ('construction', 'concordance_select'): 'Select concordance branch', ('construction', 'epoch_elapsed'): 'Elapsed epoch quantity',
    ('construction', 'epoch_inclusive'): 'Inclusive epoch count', ('construction', 'era_index'): 'Era index',
    ('construction', 'loop_result'): 'Loop result', ('construction', 'nominal'): 'Nominal expression',
    ('construction', 'obscuration_index'): 'Obscuration-cycle index', ('construction', 'temporal_anchor'): 'Temporal reference',
    ('construction', 'year_name'): 'Name year', ('construction', 'unclassified'): 'Unclassified expression',

    ('syntax', 'UnsupportedConstruction'): 'Unparsed construction', ('syntax', 'Sequence'): 'Construction sequence',
    ('syntax', 'Term'): 'Term candidate', ('syntax', 'Number'): 'Numeral candidate',
    ('syntax', 'Anaphor'): 'Anaphoric candidate', ('syntax', 'Syntax'): 'Low-level syntax edge',
    ('frame', 'ProcedureDef'): 'Procedure', ('frame', 'QueryDef'): 'Calculation stage',
    ('frame', 'MethodSlice'): 'Reusable method', ('frame', 'ContextDef'): 'Background context',

    ('port', 'result'): 'Result', ('port', 'value'): 'Operand', ('port', 'left'): 'Left operand',
    ('port', 'right'): 'Right operand', ('port', 'dividend'): 'Dividend', ('port', 'divisor'): 'Divisor',
    ('port', 'quotient'): 'Quotient', ('port', 'remainder'): 'Remainder', ('port', 'lower'): 'Lower bound',
    ('port', 'offset'): 'Offset', ('port', 'origin'): 'Counting origin', ('port', 'cycle'): 'Cycle length',
    ('port', 'amount'): 'Increment', ('port', 'receiver'): 'Receiver', ('port', 'label'): 'Name',
    ('port', 'marker'): 'Heading marker', ('port', 'target'): 'Target', ('port', 'decrement'): 'Decrement',
    ('port', 'factor'): 'Multiplier', ('port', 'denominator'): 'Denominator', ('port', 'numerator'): 'Numerator',
    ('port', 'whole'): 'Whole part',

    ('role', 'external_input'): 'External input', ('role', 'root_input'): 'Root input',
    ('role', 'missing_upstream'): 'Upstream source missing', ('role', 'parameter'): 'Parameter',
    ('role', 'literal'): 'Literal value', ('role', 'predicate'): 'Judgment result',
    ('role', 'quotient'): 'Quotient', ('role', 'remainder'): 'Remainder',
    ('role', 'result'): 'Result', ('role', 'accumulator'): 'Accumulator', ('role', 'offset'): 'Offset',
    ('lexical_role', 'term'): 'Term', ('lexical_role', 'numeral'): 'Numeral',
    ('lexical_role', 'pronoun'): 'Pronoun', ('lexical_role', 'function_word'): 'Function word',
    ('lexical_role', 'preposition'): 'Preposition', ('lexical_role', 'particle'): 'Particle',
    ('lexical_role', 'operator_cue'): 'Operation cue',
    ('candidate_state', 'proposed'): 'Machine proposal', ('candidate_state', 'selected'): 'Used by machine compile',
    ('candidate_state', 'rejected'): 'Excluded from current compile', ('candidate_state', 'unresolved'): 'Not yet lowered',

    ('cause', 'unresolved_parser'): 'Source text not yet parsed', ('cause', 'incomplete_construction'): 'Construction incomplete',
    ('cause', 'missing_import'): 'Input source missing', ('cause', 'unknown_quantity_semantics'): 'Quantity meaning unresolved',
    ('cause', 'unknown_quantity'): 'Quantity unidentified', ('cause', 'stale_identity'): 'Runtime version changed',
    ('cause', 'stale_source'): 'Source version changed', ('cause', 'multiple_active_decisions_for_slot'): 'Conflicting review decisions',
    ('cause', 'schema_extension_required'): 'Type system insufficient', ('cause', 'binding_not_structurally_compatible'): 'Binding incompatible',
    ('cause', 'necessary_source_not_accounted'): 'Source text not yet accounted for', ('cause', 'requires_external_data'): 'External source required',
    ('cause', 'missing_query_base'): 'Calculation base missing', ('cause', 'ambiguous_import'): 'Multiple possible quantity sources',
    ('cause', 'ambiguous_operation_import'): 'Multiple possible operation sources', ('cause', 'missing_operation_import'): 'Operation source missing',
    ('cause', 'UnsupportedConstruction'): 'Construction unsupported', ('cause', 'unclassified'): 'Expression unclassified',
    ('cause', 'unresolved'): 'Still unresolved', ('cause', 'quantity_unresolved'): 'Quantity unresolved',
    ('cause', 'invalid_human_decision'): 'Review decision invalid', ('cause', 'invalid_quantity_semantics'): 'Quantity interpretation invalid',
    ('cause', 'invalid_parameter_declaration'): 'Parameter declaration invalid', ('cause', 'requires_conversion_evidence'): 'Conversion evidence required',
    ('cause', 'truncated_candidate_set'): 'Candidate set incomplete', ('cause', 'graph_not_closed'): 'Data-flow graph incomplete',
    ('cause', 'required_control_marked_noncomputational'): 'Required control text excluded', ('cause', 'incompatible_units'): 'Units incompatible',
    ('cause', 'incompatible_time_origin'): 'Time origins incompatible', ('cause', 'compatible'): 'Structurally compatible',
    ('cause', 'upstream_segmentation_changed'): 'Source segmentation changed', ('cause', 'context_candidate_set_changed'): 'Context candidates changed',
    ('cause', 'missing_dependency'): 'Required dependency missing', ('cause', 'dependency_retracted'): 'Required dependency retracted',
    ('cause', 'unknown_retraction_target'): 'Retraction target missing', ('cause', 'missing_read_port'): 'Required input port missing',
    ('cause', 'dangling_read'): 'Input reference unresolved', ('cause', 'invalid_output_port'): 'Output port inconsistent',
    ('cause', 'lost_division_port'): 'Division output incomplete', ('cause', 'missing_source'): 'Source evidence missing',
    ('cause', 'invalid_source_span'): 'Source span invalid', ('cause', 'missing_producer'): 'Quantity producer missing',
    ('cause', 'cross_query_dependency'): 'Cross-stage dependency unresolved', ('cause', 'invalid_time_frame'): 'Time frame inconsistent',
    ('cause', 'remainder_producer_corruption'): 'Remainder source inconsistent', ('cause', 'full_accumulation_corruption'): 'Accumulation source inconsistent',
    ('cause', 'parameter_identity_corruption'): 'Parameter source inconsistent', ('cause', 'dependency_cycle'): 'Dependency cycle',

    ('issue', 'missing_input'): 'Input needs a source', ('issue', 'no_legal_candidate'): 'Construction needs review',
    ('issue', 'quantity_semantics'): 'Quantity meaning needs review', ('issue', 'stale_session'): 'Review session needs revalidation',
    ('issue', 'decision_conflict'): 'Review decisions conflict', ('issue', 'invalid_review_binding'): 'Binding failed validation',
    ('issue', 'ontology_extension_required'): 'Type system needs extension', ('issue', 'producer_or_port_ambiguity'): 'Quantity source is ambiguous',
    ('issue', 'missing_context_or_profile'): 'Background information missing', ('issue', 'invalid_graph_structure'): 'Data-flow structure invalid',
    ('issue', 'stale_decision'): 'Decision needs revalidation', ('issue', 'uncovered_source'): 'Source text still unexplained',
    ('issue', 'invalid_human_decision'): 'Review decision did not apply',

    ('action', 'select_candidate'): 'Accept candidate', ('action', 'reject_candidate'): 'Reject candidate',
    ('action', 'resegment'): 'Change span', ('action', 'set_scope'): 'Set calculation scope',
    ('action', 'bind_value'): 'Bind quantity source', ('action', 'bind_call'): 'Bind method call',
    ('action', 'set_quantity_semantics'): 'Describe quantity', ('action', 'select_profile'): 'Select interpretation',
    ('action', 'attach_context'): 'Add context source', ('action', 'declare_parameter'): 'Declare external parameter',
    ('action', 'assemble_known_structure'): 'Add known construction', ('action', 'mark_noncomputational'): 'Mark as non-computational',
    ('action', 'defer'): 'Leave unresolved', ('action', 'approve_scope'): 'Approve scope',
    ('action', 'retract'): 'Retract decision', ('action', 'set_lexical_role'): 'Set lexical role',

    ('unit', 'integer'): 'Integer', ('unit', 'year'): 'Year', ('unit', 'year_ordinal'): 'Year ordinal',
    ('unit', 'year_index'): 'Year index', ('unit', 'month'): 'Month', ('unit', 'month_fraction'): 'Fraction of a month',
    ('unit', 'day'): 'Day', ('unit', 'day_fraction'): 'Fraction of a day', ('unit', 'du'): 'Degree (du)',
    ('unit', 'du_fraction'): 'Fraction of a degree', ('unit', 'boolean'): 'Boolean', ('unit', 'status'): 'Status',
    ('unit', 'opaque'): 'Unit unresolved', ('unit', 'product'): 'Product unit unresolved', ('unit', 'unknown'): 'Unit unknown',
    ('unit', 'cycle'): 'Cycle count', ('unit', 'ordinal'): 'Ordinal position', ('unit', 'month_ordinal'): 'Month ordinal',
    ('unit', 'month_name_index'): 'Month-name index', ('unit', 'intercalary_month'): 'Intercalary-month count',
    ('unit', 'medial'): 'Medial-qi count', ('unit', 'medial_fraction'): 'Fraction of a medial qi',
    ('unit', 'station'): 'Station index', ('unit', 'station_fraction'): 'Fraction of a station',
    ('unit', 'planet_event'): 'Planetary-event count', ('unit', 'table_column'): 'Table-column index',
    ('unit', 'day_index'): 'Day index', ('unit', 'boundary_status'): 'Boundary status',
    ('unit', 'epoch_identity'): 'Epoch reference', ('unit', 'event_sequence'): 'Event sequence',
    ('quantity_kind', 'count'): 'Count', ('quantity_kind', 'duration'): 'Duration', ('quantity_kind', 'angle'): 'Angle',
    ('quantity_kind', 'predicate'): 'Judgment', ('quantity_kind', 'status'): 'Status', ('quantity_kind', 'reference'): 'Reference',
    ('quantity_kind', 'sequence'): 'Sequence', ('quantity_kind', 'unknown'): 'Type unresolved',
    ('representation', 'whole'): 'Whole-unit value', ('representation', 'fraction_numerator'): 'Fraction numerator',
    ('representation', 'fraction'): 'Fraction',
    ('evidence', 'text_overt'): 'Explicit in source', ('evidence', 'declared_edited'): 'Edited reading',
    ('evidence', 'mechanically_derived'): 'Mechanically derived', ('evidence', 'source_explicit'): 'Source evidence',
    ('evidence', 'parser_rule'): 'Parser rule', ('evidence', 'human_selected'): 'Selected by researcher',
    ('evidence', 'human_constructed'): 'Constructed by researcher', ('evidence', 'scholarship'): 'Scholarly interpretation',
    ('evidence', 'scripted_fixture'): 'Automated test fixture', ('evidence', 'human'): 'Researcher action', ('evidence', 'agent'): 'Agent action',
    ('resolution_state', 'resolved'): 'Resolved', ('resolution_state', 'unknown'): 'Unresolved',
    ('graph_state', 'closed'): 'Data flow complete', ('graph_state', 'partial'): 'Data flow incomplete',
    ('graph_state', 'invalid'): 'Structure invalid', ('graph_state', 'compiled'): 'Structure compiled', ('graph_state', 'issues'): 'Needs review',
    ('review_state', 'draft'): 'Draft', ('review_state', 'in_review'): 'In review', ('review_state', 'approved'): 'Review recorded',
    ('review_state', 'needs_review'): 'Needs review', ('review_state', 'completed'): 'Review queue completed', ('review_state', 'needs_revalidation'): 'Needs revalidation',
    ('execution_state', 'not_run'): 'Not executed', ('execution_state', 'not_requested'): 'Execution not requested',
    ('execution_state', 'missing_inputs'): 'Inputs missing', ('execution_state', 'unresolved'): 'Execution blocked by unresolved items',
    ('execution_state', 'unsupported'): 'Execution unsupported', ('execution_state', 'failed'): 'Execution failed', ('execution_state', 'executed'): 'Execution completed',
    ('comparison_state', 'unavailable'): 'No independent comparison', ('comparison_state', 'exact'): 'Exact match',
    ('comparison_state', 'compatible'): 'Compatible', ('comparison_state', 'mismatch'): 'Mismatch',
    ('comparison_state', 'blocked'): 'Comparison blocked', ('comparison_state', 'scoped_ready'): 'Scope ready for comparison', ('comparison_state', 'ready'): 'Ready for comparison',
    ('session_state', 'ok'): 'Session current', ('session_state', 'stale_source'): 'Source changed',
    ('session_state', 'stale_identity'): 'Runtime changed', ('session_state', 'active'): 'Active decision',
    ('session_state', 'retracted'): 'Retracted decision', ('session_state', 'conflicted'): 'Conflicting decision', ('session_state', 'needs_revalidation'): 'Needs revalidation',
    ('stage_state', 'not_run'): 'Not run', ('stage_state', 'processing'): 'Processing',
    ('stage_state', 'completed'): 'Analysis produced', ('stage_state', 'needs_review'): 'Needs review',
    ('stage_state', 'blocked'): 'Blocked', ('stage_state', 'stale'): 'Stale',
    ('severity', 'blocking'): 'Blocking', ('severity', 'review'): 'Review required',
    ('artifact', 'source_packet'): 'Analysis input', ('artifact', 'documents'): 'Source documents',
    ('artifact', 'tokens'): 'Lexical candidates', ('artifact', 'construction_candidates'): 'Construction candidates',
    ('artifact', 'definitions'): 'Calculation structure', ('artifact', 'values'): 'Quantities',
    ('artifact', 'events'): 'Operations', ('artifact', 'graph_status'): 'Data-flow status',
    ('artifact', 'unresolved_required_spans'): 'Unexplained required source', ('artifact', 'review_questions'): 'Review questions',
    ('validation_state', 'true'): 'Ready for complete export', ('validation_state', 'false'): 'Complete export blocked',
    ('control_end', 'judgment'): 'End at judgment', ('symbol', 'unresolved_focus'): 'Current operand unresolved',
}


def _register_english(category, rows):
    for line in rows.strip().splitlines():
        code, definition_en = line.strip().split('|', 1)
        _DEFINITION_EN[category, code] = definition_en


_register_english('operation', '''
input|Provides a quantity through an input node in the graph.
literal|Creates a value from a numeral in the source text.
parameter|Supplies a parameter from a compiled background declaration.
load|Makes an input quantity the current operand.
multiply|Reads two operands and produces their product.
add|Reads two operands and produces their sum.
subtract|Produces a difference from the recorded left and right operands.
divmod|Produces separate quotient and remainder outputs from a division.
cycle_reduce|Divides by a recorded cycle quantity and retains quotient and remainder.
alias|Creates a named reference to an existing quantity.
threshold|Tests a recorded quantity against a recorded boundary.
count|Counts from a recorded origin using a recorded offset.
year_scan|Subtracts month counts through an existing sequence of year lengths.
interval_scale|Scales an interval by a recorded multiplier.
method_call|Calls an already compiled method through recorded ports.
select|Chooses an output using an existing condition.
lookup|Reads data from an existing table row and column.
rescale|Changes a quantity's representation scale using recorded evidence.
fraction|Forms a fraction from a whole part, numerator, and denominator.
convert|Converts units using a recorded rate.
epoch_frame|Establishes a recorded epoch reference.
repeat|Runs an established repeated body with a stopping condition.
cycle_lift|Uses an existing model to lift a residual quantity into a full local epoch coordinate.
event_sequence|Generates an ordered event sequence from a recorded origin and interval.
boundary_call|Compares using the selected boundary interpretation.
framed_origin|Places an origin within a recorded epoch frame.
initial_instant|Establishes an initial instant from a recorded interpretation.
judgment|Records the result of an existing judgment.
''')

_register_english('construction', '''
task_marker|Text identified as an entry point for a procedure.
query_marker|Text identified as an entry point for a query.
update_count|An expression combining a quantity update with counting.
numeral_predicate|An expression in which a numeral cues multiplication.
denominator_declaration|An expression specifying a denominator for subsequent calculation.
multiply|An expression with a multiplication construction.
multiply_focus|A multiplication expression whose operand is the current quantity.
subtract|An expression with a subtraction construction.
update|An expression that explicitly updates a receiver quantity.
pair_increment|An expression linking a name with an increment.
load|An expression that loads an operand.
divide|An expression that divides by a specified divisor to obtain quotient and remainder.
cycle_divide|An expression that removes complete cycles by division.
divide_by|An expression explicitly naming a divisor and a dividend.
pending_cycle|A recognized expression that needs a following construction to determine its calculation.
loop_threshold|An expression marking a boundary in a repeated process.
remainder_name|An expression that names a remainder quantity.
name|An expression that names a quantity.
receiver_add|An expression that combines a current quantity into a receiver.
count_origin|An expression stating where counting begins.
count_command|An expression directing counting from an origin.
count_remainder|An expression that counts from a remainder quantity.
threshold|An expression stating a boundary relation.
add|An expression stating that a quantity is added.
recur_increment|An expression stating a subsequent increment.
double_interval|An expression stating that an interval is doubled.
mixed_compact|A compact expression with whole and fractional parts.
declaration|An expression linking a name and a literal value.
parameter_alias|An expression assigning another name to a background quantity.
mixed_duration|A duration expression with whole and fractional parts.
reuse_operation|An expression referring to an earlier operation.
epoch_load|An expression loading years counted from an epoch.
method_value_reference|An expression referring to a method that processes a quantity.
scalar_value|An expression declaring a scalar value.
scalar_name|An expression naming a scalar.
schedule_row|An expression recording a relation between years and cumulative counts.
scan_length|An expression recording a length to be repeatedly subtracted.
epoch_divide|A division performed on a quantity accumulated from an epoch.
entry_cycle|An expression recording the reduction step that enters a cycle.
entry_remainder_divide|An expression continuing division of the remainder on entry to a cycle.
concordance_case|An expression recording one branch of a concordance calculation.
conditional_count|An expression that counts when a condition is met.
method_reference|An expression referring to the preceding method.
use_denominator|An expression using a denominator stated earlier.
complete_cycle|The continuation recognized for a cycle-reduction construction.
judgment|An expression recording a judgment conclusion.
annotation|Explanatory text recognized by a rule.
boundary|An expression concerning an event boundary.
concordance_pending|A concordance expression awaiting subsequent structure.
concordance_remainder|A remainder expression within a concordance calculation.
concordance_select|A selection expression within a concordance calculation.
epoch_elapsed|An expression for a quantity elapsed from an epoch.
epoch_inclusive|An epoch count that includes its starting position.
era_index|An expression for an era index.
loop_result|An expression recording the result of a repeated process.
nominal|An expression currently identified as nominal.
obscuration_index|An expression for an obscuration-cycle index.
temporal_anchor|An expression specifying a temporal reference.
year_name|An expression assigning a name to a year.
unclassified|An expression for which the current rule assigns no category.
''')

_register_english('syntax', '''
UnsupportedConstruction|A construction the current rules do not explain.
Sequence|A sequence of constructions in recorded order.
Term|A lexical item occurrence recognized at this location.
Number|A numeral occurrence recognized at this location.
Anaphor|An anaphoric expression recognized at this location.
Syntax|A syntactic edge recognized at this location.
''')

_register_english('frame', '''
ProcedureDef|A procedure range recorded by the program structure.
QueryDef|A query or calculation stage established from an existing base state.
MethodSlice|A compiler-extracted range that can be referenced as a method.
ContextDef|A range that provides background declarations.
''')

_register_english('cause', '''
unresolved_parser|The current rules do not explain this source segment.
incomplete_construction|The current construction awaits a rule-required continuation.
missing_import|A required input has not been bound.
unknown_quantity_semantics|The meaning of the quantity remains to be determined.
unknown_quantity|The current structure cannot identify the referenced quantity.
stale_identity|Existing review decisions must be revalidated because the runtime identity changed.
stale_source|Existing review decisions must be revalidated because the source version changed.
multiple_active_decisions_for_slot|The same judgment target has conflicting active decisions.
schema_extension_required|The current type catalogue cannot express the required structure.
binding_not_structurally_compatible|The specified binding fails the backend structural check.
necessary_source_not_accounted|This source span has not yet been structurally accounted for.
requires_external_data|The current operation still requires sourced external material.
missing_query_base|The current query has no determined base state.
ambiguous_import|The current quantity has more than one candidate source.
ambiguous_operation_import|The current operation has more than one candidate source.
missing_operation_import|The current operation refers to an unbound input.
UnsupportedConstruction|The current rules do not explain this source segment.
unclassified|The current rules assign no category to this expression.
unresolved|The current structure still contains unexplained content.
quantity_unresolved|The meaning of the quantity remains to be determined.
invalid_human_decision|The current decision does not pass compilation checks.
invalid_quantity_semantics|The quantity description does not satisfy current constraints.
invalid_parameter_declaration|This quantity cannot be treated as a root input under the current declaration.
requires_conversion_evidence|The conversion still needs explicit evidence.
truncated_candidate_set|The current record does not contain the complete candidate set.
graph_not_closed|The graph does not satisfy the closure conditions for complete export.
required_control_marked_noncomputational|A required control span is marked as non-computational.
incompatible_units|The two units do not pass compatibility checks.
incompatible_time_origin|The two temporal references do not pass compatibility checks.
compatible|This structural compatibility check passed.
upstream_segmentation_changed|The decision depends on a segmentation that changed upstream.
context_candidate_set_changed|The decision depends on a background candidate set that changed.
missing_dependency|A required upstream decision is absent from the current branch.
dependency_retracted|A required upstream decision was retracted.
unknown_retraction_target|The current branch does not contain the requested retraction target.
missing_read_port|The operation lacks a required input port.
dangling_read|The referenced input quantity is absent from the current graph.
invalid_output_port|The quantity's producer and recorded output port do not agree.
lost_division_port|The division does not retain both required quotient and remainder ports.
missing_source|The node has no recorded source evidence.
invalid_source_span|The node span does not match the current source text.
missing_producer|A derived quantity has no producer in the current graph.
cross_query_dependency|A cross-query quantity reference did not pass verification.
invalid_time_frame|The current temporal frame did not pass structural checks.
remainder_producer_corruption|The remainder name points to a different output port.
full_accumulation_corruption|The accumulation receiver does not agree with the explicit name.
parameter_identity_corruption|The parameter does not originate from a declaration node.
dependency_cycle|The current dependency relation contains a cycle.
''')


def _register(category, rows, required, prohibited, parent=None):
    for line in rows.strip().splitlines():
        code, label, definition = line.strip().split('|', 2)
        definition_en = _DEFINITION_EN.get((category, code))
        if category in INSPECTOR_DEFAULT_CATEGORIES and not definition_en:
            raise ValueError(f'missing_english_definition:{category}:{code}')
        REGISTRY[category, code] = {
            'code': code, 'category': category, 'hierarchy': [category, parent, code] if parent else [category, code],
            'label': label, 'label_en': _LABEL_EN.get((category, code)), 'definition': definition,
            'definition_en': definition_en,
            'methodology': definition + '；此名称描述后端记录的类型或状态，须结合原文证据与依赖检查阅读。',
            'required_fields': list(required), 'must_not_infer': list(prohibited),
        }


def entry(category, code):
    try:
        return deepcopy(REGISTRY[category, code])
    except KeyError:
        raise ValueError(f'unregistered_ontology_code:{category}:{code}') from None


def codes(category):
    return {code for domain, code in REGISTRY if domain == category}


def label(category, code):
    return entry(category, code)['label']


def label_en(category, code):
    value = entry(category, code)['label_en']
    if not value:
        raise ValueError(f'missing_english_label:{category}:{code}')
    return value


_register('operation', '''
input|外部输入|由图中输入节点提供的数量
literal|原文字面数|根据原文数词生成的数值
parameter|背景参数|来自已编译背景声明的参数
load|置入数量|将输入量置为当前操作对象
multiply|相乘|读取两个操作数并生成乘积
add|相加|读取两个操作数并生成和
subtract|相减|按已记录左右操作数生成差
divmod|整除并保留余数|生成独立的商与余数输出
cycle_reduce|按周期取商余|按记录的周期量进行整除
alias|命名数量|为已有量建立名称引用
threshold|阈值判断|按图中记录的量与界限作判断
count|从起点计数|按记录的起点和偏移计数
year_scan|逐年扣除|按既有年长序列扣除月数
interval_scale|间隔倍乘|以记录的倍数缩放间隔
method_call|调用已有方法|通过记录的端口调用已编译的方法
select|分支选择|根据已有条件选取输出
lookup|表格读取|按现有表的行列读取数据
rescale|换分母表示|依据已有证据改变数量的表示尺度
fraction|组合分数量|由整数部分、分子及分母组成分数量
convert|单位转换|依据已记录的率转换单位
epoch_frame|时间原点框架|建立已记录的历元参照
repeat|有界重复|执行已建立的重复体与停止条件
cycle_lift|周期坐标提升|按已有模型将余量转换到完整局部历元坐标
event_sequence|生成事件序列|根据已有起点与间隔生成序列
boundary_call|边界判定调用|使用已选择的边界解释进行比较
framed_origin|带参照的起点|将起点放入已记录的历元框架
initial_instant|初始时刻|依据已有解释建立初始时刻
judgment|判断结果|记录已有判断的结果
''', ('kind', 'reads', 'writes', 'source_spans'), ('节点存在不等于语义正确', '能执行不等于历史解释成立'))

_register('construction', '''
task_marker|过程标题候选|识别为过程入口的文字
query_marker|查询标题候选|识别为查询入口的文字
update_count|更新与计数候选|组合更新数量和计数的表达
numeral_predicate|数词倍乘候选|数词充当倍乘提示的表达
denominator_declaration|分母声明候选|指定后续计算分母的表达
multiply|相乘候选|具有相乘构式的表达
multiply_focus|当前量倍乘候选|以当前量为操作对象的相乘表达
subtract|相减候选|具有相减构式的表达
update|接收量更新候选|明确更新某接收量的表达
pair_increment|成对增量候选|将名称与增量联系起来的表达
load|置入候选|置入一个操作对象的表达
divide|整除候选|按指定除数求商余的表达
cycle_divide|周期消去候选|按周期除去整份的表达
divide_by|除去候选|明确除数与被除对象的表达
pending_cycle|待续周期构式|当前识别需要后续构式才能确定计算
loop_threshold|重复界限候选|重复过程中的界限表达
remainder_name|余数命名候选|给余量命名的表达
name|数量命名候选|给数量命名的表达
receiver_add|归并到接收量候选|将当前量归并到某接收量的表达
count_origin|计数起点候选|说明计数从何处开始的表达
count_command|计数指令候选|指示从某起点命数的表达
count_remainder|余数计数候选|以余量进行计数的表达
threshold|阈值候选|说明界限关系的表达
add|相加候选|说明增加一个量的表达
recur_increment|递次增量候选|说明后续增量的表达
double_interval|间隔加倍候选|说明间隔加倍的表达
mixed_compact|混合量候选|紧凑书写的整数与分数部分
declaration|背景声明候选|将名称与字面量联系起来的表达
parameter_alias|背景别名候选|给背景量另设名称的表达
mixed_duration|混合时长候选|包含整数与分数部分的时长表达
reuse_operation|复用操作候选|指向先前操作的表达
epoch_load|历元年数候选|置入从历元起算年数的表达
method_value_reference|方法量引用候选|引用已有方法处理一个量的表达
scalar_value|标量声明候选|声明一个标量数值的表达
scalar_name|标量命名候选|给标量命名的表达
schedule_row|历表行候选|记录年数与累计数对应关系的表达
scan_length|扣除长度候选|记录逐次扣除长度的表达
epoch_divide|历元除法候选|对历元累计量作除法的表达
entry_cycle|进入周期候选|记录进入周期的消去步骤
entry_remainder_divide|进入余量除法候选|继续处理进入周期余量的表达
concordance_case|配合分支候选|记录配合步骤某分支的表达
conditional_count|条件计数候选|条件满足后计数的表达
method_reference|方法引用候选|指向前述算法的表达
use_denominator|沿用分母候选|使用此前已给分母的表达
complete_cycle|周期构式续部|当前规则识别到周期消去的续部
judgment|判断结论候选|记录判断结论的表达
annotation|说明性构式候选|由规则识别的说明文字
boundary|边界构式候选|涉及事件边界的表达
concordance_pending|待续配合候选|当前配合表达等待后续结构
concordance_remainder|配合余数候选|配合计算中的余量表达
concordance_select|配合选择候选|配合计算中的选择表达
epoch_elapsed|历元经过量候选|自历元经过的数量表达
epoch_inclusive|历元包含计数候选|包含起始位置的历元计数表达
era_index|纪序号候选|关于纪的序号表达
loop_result|重复结果候选|记录重复过程结果的表达
nominal|名词性候选|当前识别为名词性结构的表达
obscuration_index|蔀序号候选|关于蔀的序号表达
temporal_anchor|时间锚点候选|指定时间参照的表达
year_name|年名候选|给年份指定名称的表达
unclassified|尚未分类的构式|当前规则未能给出可降译的构式
''', ('kind', 'source_spans'), ('candidate 不等于 confirmed', '附近证据不等于合法替代项'))

# AST names are aliases in the formal grammar. Their descriptions retain the
# candidate qualification; this does not declare a parse historically confirmed.
for construction, syntax_kind, _ in GRAMMAR:
    if ('syntax', syntax_kind) not in REGISTRY:
        original = entry('construction', construction)
        REGISTRY['syntax', syntax_kind] = {**original, 'code': syntax_kind, 'category': 'syntax',
                                          'hierarchy': ['syntax', 'construction', syntax_kind]}
for construction in codes('construction'):
    original = entry('construction', construction)
    REGISTRY.setdefault(('syntax', construction.title()), {**original, 'code': construction.title(),
                         'category': 'syntax', 'hierarchy': ['syntax', 'reviewed_construction', construction.title()]})
_register('syntax', '''
UnsupportedConstruction|未解释的构式|当前规则未能解释的结构
Sequence|有序构式组|按既有次序排列的构式
Term|词项|当前识别的词项出现
Number|数词|当前识别的数词出现
Anaphor|指代项|当前识别的指代表达
Syntax|语法成分|当前识别的语法成分
''', ('kind', 'source_spans'), ('未解释不等于原文错误', '词项不等于计算操作'))
_register('frame', '''
ProcedureDef|过程|由程序结构记录的过程范围
QueryDef|查询或阶段|在既有基态上建立的查询或阶段
MethodSlice|方法片段|编译器提取的可引用方法范围
ContextDef|背景范围|提供背景声明的范围
''', ('kind', 'source_spans'), ('过程范围覆盖不等于内部语义已解释',))

_register('issue', '''
missing_input|输入待绑定|所需输入尚未绑定
no_legal_candidate|构式待解释|当前编译未形成可用解释
quantity_semantics|数量含义待审|数量含义尚待确定
stale_session|会话待重验|已有审定需要重新核验
decision_conflict|决定冲突|同一判断对象存在冲突决定
invalid_review_binding|绑定不兼容|当前绑定未通过结构兼容检查
ontology_extension_required|类型目录待扩展|现有类型目录需要扩展
producer_or_port_ambiguity|数量来源或端口待确定|编译器报告数量来源或端口需要判断
missing_context_or_profile|背景或解释方案待补|当前计算缺少所需背景或解释方案
invalid_graph_structure|图结构检查未通过|已建立的图未满足结构约束
stale_decision|决定待重验|上游变化后该决定需要重新核验
uncovered_source|原文尚未纳入结构|仍有必要原文尚未被结构说明
invalid_human_decision|人工决定未生效|该决定未通过当前编译检查
''', ('kind', 'reason', 'severity'), ('unresolved 不等于错误', 'blocking 不等于史料错误'))
_register('cause', '''
unresolved_parser|规则未能解释|当前规则未能解释这段文字
incomplete_construction|构式待续|当前构式尚待规则要求的后续部分
missing_import|输入缺少来源|所需输入尚未绑定
unknown_quantity_semantics|数量语义未定|数量含义尚待确定
unknown_quantity|数量尚未识别|当前结构未能确定所引用的数量
stale_identity|运行版本已变化|已有审定需要重新核验
stale_source|来源版本已变化|已有审定需要重新核验
multiple_active_decisions_for_slot|活动决定互斥|同一判断对象存在冲突决定
schema_extension_required|类型表达不足|现有类型目录需要扩展
binding_not_structurally_compatible|绑定结构不兼容|指定的绑定未通过后端结构检查
necessary_source_not_accounted|必要原文未说明|该跨度尚未被结构说明
requires_external_data|需要外部材料|当前操作仍需有来源的外部材料
missing_query_base|查询基态未定|当前查询尚未确定其基态
ambiguous_import|多个数量来源|当前数量存在多个来源候选
ambiguous_operation_import|多个操作来源|当前操作存在多个来源候选
missing_operation_import|操作来源缺失|当前操作引用尚未绑定
UnsupportedConstruction|构式未受支持|当前规则未能解释这段文字
unclassified|尚未分类|当前规则未给该表达确定类别
unresolved|尚未解释|当前结构仍有未解释内容
quantity_unresolved|数量语义未定|数量含义尚待确定
invalid_human_decision|人工决定未生效|当前决定未通过编译检查
invalid_quantity_semantics|数量说明未通过检查|数量说明未满足现有约束
invalid_parameter_declaration|根输入声明未通过检查|该量不能按当前声明视为根输入
requires_conversion_evidence|转换缺少依据|转换仍需明确证据
truncated_candidate_set|候选集合不完整|当前记录没有完整候选集合
graph_not_closed|图尚未闭合|图未满足完整导出所需的闭合条件
required_control_marked_noncomputational|必要控制被排除|必要控制跨度被标为非计算内容
incompatible_units|单位不兼容|两侧单位未通过兼容检查
incompatible_time_origin|时间原点不兼容|两侧时间参照未通过兼容检查
compatible|符合兼容检查|本次结构兼容检查通过
upstream_segmentation_changed|上游切分变化|该决定依赖的切分已变化
context_candidate_set_changed|背景候选变化|该决定依赖的背景候选已变化
missing_dependency|依赖决定缺失|所需上游决定未出现在当前分支
dependency_retracted|依赖决定已撤销|所需上游决定已被撤销
unknown_retraction_target|撤销对象不存在|当前分支中未找到该撤销对象
missing_read_port|必要输入端口缺失|操作缺少必须的输入端口
dangling_read|输入引用悬空|输入引用的数量不在当前图中
invalid_output_port|输出端口不一致|数量的生产者与输出端口记录不一致
lost_division_port|商余端口不完整|除法没有同时保留所需商余端口
missing_source|缺少原文证据|节点未记录原文证据
invalid_source_span|原文坐标不一致|节点跨度与当前原文不一致
missing_producer|数量没有生产者|派生量缺少当前图中的生产者
cross_query_dependency|跨查询引用未证实|数量跨查询引用未通过检查
invalid_time_frame|时间框架不一致|当前时间框架未通过结构检查
remainder_producer_corruption|余数来源不一致|余数命名指向了其他输出端口
full_accumulation_corruption|累计量来源不一致|累计量接收对象与显式名称不一致
parameter_identity_corruption|参数来源不一致|参数没有来自声明节点
dependency_cycle|依赖成环|当前依赖关系含有循环
''', ('cause or kind or reason',), ('expected continuation 不等于原文省略', 'unknown 不等于 wrong', '缺少计算输入不等于史料缺字'))

_register('action', '''
select_candidate|选择已有候选|记录研究者选择的现有候选
reject_candidate|拒绝候选|记录研究者排除的候选
resegment|重新切分|按当前原文字符边界重新划分跨度
set_scope|调整范围与基态|指定已有过程范围及查询基态
bind_value|绑定数量来源与端口|指定所需数量的生产者及输出端口
bind_call|绑定过程调用|指定过程调用的来源
set_quantity_semantics|说明数量含义与尺度|记录数量的类型、单位和尺度判断
select_profile|选择解释方案|选择已登记的解释方案
attach_context|补充背景来源|将有来源的背景文档加入编译输入
declare_parameter|声明合法根输入|声明需要外部提供的根输入
assemble_known_structure|构造已有类型|用现有有限目录填写结构槽
mark_noncomputational|标记说明性文字|以证据和理由将跨度标为非计算内容
defer|保留未决|保存当前尚不能确定的判断
approve_scope|审定指定范围|记录研究者对指定范围的审定
retract|撤销决定|撤销已有决定并重新编译
set_lexical_role|修正当前词项功能|记录当前出现处的语法功能判断
''', ('action', 'targets', 'payload'), ('动作列出不等于已经执行', '人工选择不等于历史事实已证明'))

_register('unit', '''
integer|整数|按整数表示的量
year|年|以年为单位的量
year_ordinal|年序数|包含计数约定的年序数
year_index|年索引|年份位置索引
month|月|以月为单位的量
month_fraction|月分量|按已记录分母表示的月量
day|日|以日为单位的量
day_fraction|日分量|按已记录分母表示的日量
du|度|以度为单位的量
du_fraction|度分量|按已记录分母表示的度量
boolean|判断值|条件判断的真假值
status|状态值|由计算步骤记录的状态
opaque|单位未解释|尚未确定可解释的单位
product|乘积单位待定|乘积尚未完成单位说明
unknown|单位未定|单位尚未确定
cycle|周期数|以周期份数记录的量
ordinal|序数|带有计数起点约定的位置
month_ordinal|月序数|月份的位置序数
month_name_index|月名索引|月名序列的位置
intercalary_month|闰月数|记录闰月的数量
medial|中气数|以中气个数记录的量
medial_fraction|中气分量|按分母表示的中气量
station|次序数|以次记录的位置
station_fraction|次分量|按分母表示的次量
planet_event|星见次数|以星见事件个数记录的量
table_column|表列索引|表中列的位置
day_index|日索引|日序列中的位置
boundary_status|边界状态|事件边界判断的状态
epoch_identity|历元参照|时间原点的标识
event_sequence|事件序列|带参照的有序事件集合
''', ('unit',), ('单位标签不提供缺失的换算率',))
_register('quantity_kind', '''
count|计数量|记录个数或序位的数量类别
duration|时长量|记录时间长度的数量类别
angle|角度量|记录角度的数量类别
predicate|判断量|记录条件判断的数量类别
status|状态量|记录计算状态的数量类别
reference|参照量|记录坐标参照的数量类别
sequence|序列量|记录有序集合的数量类别
unknown|类型未定|数量类别尚未确定
''', ('quantity_kind',), ('类型未定不等于数量错误',))
_register('role', '''
external_input|外部输入|需要外部提供的输入量
root_input|根输入|被明确声明的根输入
missing_upstream|上游来源待定|当前量尚缺所需的上游来源
parameter|背景参数|来自背景声明的量
literal|原文字面数|来自数词的量
predicate|判断结果|来自条件判断的量
quotient|商|来自整除商端口的量
remainder|余数|来自整除余数端口的量
result|结果量|操作的结果端口
accumulator|累计量|当前结构记录的累计接收量
offset|偏移量|相对于某参照的偏移
''', ('role',), ('数量角色不等于词的语法功能',))
_register('representation', '''
whole|整量表示|以完整单位表示
fraction_numerator|分子表示|须结合指定分母理解的分子
fraction|分数表示|由分子与分母共同表示
''', ('representation.kind',), ('分子数字不等于完整数量',))

_register('resolution_state', '''
resolved|当前约束已确定|当前数量约束已得到说明
unknown|尚待确定|当前信息尚不能确定该项
''', ('resolution_status',), ('已确定不等于历史解释已获证明', '未知不等于错误'))
_register('graph_state', '''
closed|结构闭合|当前图满足闭合检查
partial|结构尚不完整|当前图仍有必要结构未确定
invalid|结构检查未通过|当前图或版本条件未满足检查
compiled|已生成结构|编译已返回结构产物
issues|存在结构问题|结构产物包含待处理问题
''', ('graph_status',), ('闭合不等于学术审定完成', '执行成功不代替闭合检查'))
_register('review_state', '''
draft|草稿|尚处于草稿状态
in_review|审定中|研究者正在审定
approved|已记录审定|指定范围有审定记录
needs_review|需要判断|仍有问题需要判断
completed|本次审核队列已处理|本次返回未列出待处理审核问题
needs_revalidation|待重新核验|已有审定需要重新核验
''', ('review_status',), ('队列为空不等于历史解释成立', 'stale 不等于 completed'))
_register('execution_state', '''
not_run|尚未核算|本次尚未请求数值核算
not_requested|尚未请求核算|本次尚未请求数值核算
missing_inputs|核算输入不足|数值核算缺少输入
unresolved|核算尚有未决项|数值核算仍有未解决依赖
unsupported|暂不支持核算|当前执行器不支持所需计算
failed|核算失败|本次数值核算失败
executed|数值核算完成|本次数值核算已返回结果
''', ('execution_status',), ('执行成功不等于解释正确',))
_register('comparison_state', '''
unavailable|暂无独立对照|当前没有可用的独立比较结果
exact|数值一致|两项给定值精确相同
compatible|符合已定兼容条件|比较符合已有兼容条件
mismatch|数值不一致|两项给定值不相同
blocked|比较受阻|尚未满足比较前提
scoped_ready|局部可比较|指定范围满足比较前提
ready|已具备比较条件|当前对象满足比较前提
''', ('comparison_status or comparisons.status',), ('同图重复计算不是独立对照',))
_register('session_state', '''
ok|版本条件通过|本次回放版本条件通过
stale_source|原文版本待重验|原文版本与会话锁不一致
stale_identity|运行版本待重验|引擎或目录版本与会话锁不一致
active|活动决定|决定参与当前回放但仍须编译检查
retracted|已撤销|决定已被撤销
conflicted|存在冲突|决定与其他活动决定冲突
needs_revalidation|待重新核验|决定需要在当前版本上重新核验
''', ('status',), ('active 不等于 applied', 'stale 不等于 completed'))
_register('stage_state', '''
not_run|尚未运行|该阶段尚未运行
processing|请求处理中|当前请求尚未返回阶段产物
completed|阶段已返回产物|该阶段已返回分析产物
needs_review|需要判断|该阶段产物包含待判断问题
blocked|受到阻断|该阶段未满足继续条件
stale|版本已陈旧|该阶段依赖的版本已变化
''', ('status',), ('处理阶段不等于原文算法步骤',))
_register('severity', '''
blocking|阻断完整审定|后端将该问题标为阻断项
review|需要研究判断|后端将该问题标为待审项
''', ('severity',), ('阻断项不等于原文错误',))
_register('lexical_role', '''
term|术语|当前出现处被记录为词项
numeral|数词|当前出现处被记录为数词
pronoun|指代词|当前出现处被记录为指代成分
function_word|功能词|当前出现处被记录为功能成分
preposition|介词|当前出现处被记录为介词
particle|助词|当前出现处被记录为助词
operator_cue|操作提示词|当前出现处被记录为操作线索
''', ('grammatical_role',), ('词的语法功能不等于整句的计算作用',))
_register('evidence', '''
text_overt|原文明示|当前节点被后端记录为原文明示
declared_edited|校读文字|当前节点使用已声明校读
mechanically_derived|机械传播|依据上游结构传播生成
source_explicit|原文证据|数量记录指向原文证据
parser_rule|规则推断|依据已登记规则识别
human_selected|人工选择|研究者选择已有候选
human_constructed|人工构造|研究者用已有类型构造结构
scholarship|学者解释|记录外部学者提供的解释
scripted_fixture|脚本验收|由自动验收脚本产生
human|研究者操作|由真实研究者操作产生
agent|代理操作|由代理操作产生
''', ('evidence_status or actor.type',), ('脚本验收不是真人试用', '机械传播不是原文明示'))
_register('port', '''
result|结果|结果输出端口
value|操作量|操作对象输入端口
left|左操作数|已记录顺序中的左侧量
right|右操作数|已记录顺序中的右侧量
dividend|被除量|除法的被除对象
divisor|除数|除法的除数
quotient|商|除法商输出
remainder|余数|除法余数输出
lower|下界|阈值下界
offset|偏移|计数偏移
origin|起点|计数起点
cycle|周期|周期长度
amount|增量|增加或扣除的量
receiver|接收量|更新接收对象
label|名称|命名对象
marker|标题提示|入口标题提示
target|目标|结构目标
decrement|减量|置入时的减量
factor|倍数|乘法倍数
denominator|分母|分数量的分母
numerator|分子|分数量的分子
whole|整数部分|混合量的整数部分
''', ('port or slot',), ('端口名称不保证绑定兼容',))

_register('profile', '''
ST_elapsed|三统历经过年计数|采用已登记的经过年计数解释
SF_Liu_inclusive|四分历包含起年计数|采用已登记的包含起年计数解释
SF_completed_four|四分历满四判断|采用已登记的满四阈值解释
instant_lunation|瞬时时刻边界|按已登记的瞬时时刻比较边界
civil_whole_day|民用整日边界|按已登记的整日比较边界
ST_intercalation_Cullen_Liu_GT|三统历严格超过界限|采用已登记的严格超过解释
ST_intercalation_GE_contrast|三统历达到界限对照|用于对照的达到界限解释
C2017_ST_Jupiter_parameter_roles_v1|三统历岁星参数解释|采用已登记的岁星参数角色解释
C2017_ST_local_year_count_v1|三统历局部年计数解释|采用已登记的局部年计数解释
C2017_ST_Jupiter_station_rate_v1|三统历岁星次率解释|采用已登记的岁星次率解释
C2017_ST_Section_four_Rules_conditional_v1|三统历四统条件解释|采用已登记的四统条件解释
C2017_ST_origin_month_day_frame_v1|三统历元月日参照|采用已登记的元月日参照解释
C2017_ST_concordance_midnight_frame_v1|三统历统首夜半参照|采用已登记的统首夜半参照解释
''', ('profile_id',), ('可选解释不等于原文唯一含义',))

_register('symbol', '''
unresolved_focus|当前操作量尚未确定|编译器尚未确定当前操作对象
''', ('labels or name',), ('未确定不等于原文省略',))
_register('action_variant', '''
defer:unresolved|保留未决|暂不消除该未决问题
defer:schema_extension_required|申请类型目录扩展|明确记录现有目录无法表达的结构
''', ('action=defer', 'payload'), ('记录请求不等于目录已经扩展',))
_register('candidate_state', '''
proposed|本次生成的候选|当前编译生成了此候选
selected|本次编译已选用|当前编译选用了此构式
rejected|本次已排除|当前编译已排除此候选
unresolved|尚无可用降译|当前候选仍不能形成完整操作
''', ('status',), ('编译选用不等于研究者确认', '候选存在不等于候选合法'))
_register('artifact', '''
source_packet|编译输入包|本次来源适配生成的编译输入
documents|来源文档|本次编译输入中的文档
tokens|词法片段|本次词法分析的产物
construction_candidates|构式候选|本次规则识别的候选
definitions|过程与范围|本次程序层记录的定义
values|数量对象|本次编译记录的量
events|操作对象|本次编译记录的操作
graph_status|图检查状态|本次完整性检查返回的状态
unresolved_required_spans|尚未说明的必要跨度|覆盖检查仍待处理的必要原文
review_questions|待审问题|本次审核队列中的问题
''', ('kind',), ('产物数量不等于解释完整性',))
_register('validation_state', '''
true|允许完整导出|后端完整导出检查通过
false|暂不能完整导出|后端完整导出检查未通过
''', ('valid_for_complete_export',), ('可导出不等于历史解释成立',))
_register('control_end', '''
judgment|判断结论处|已记录的控制范围在判断结论处结束
''', ('scope_end',), ('范围结束不等于判断正确',))
