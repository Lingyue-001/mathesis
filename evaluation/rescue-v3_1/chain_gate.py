"""End-to-end source-goal gate, separate from the fixed obligation score."""
import importlib.util
from pathlib import Path
S=importlib.util.spec_from_file_location('chain_evidence',Path(__file__).with_name('evidence_contracts.py'))
evidence=importlib.util.module_from_spec(S);S.loader.exec_module(evidence)


def assess(packet,report,execution,score,contract,graph_class):
    from fixed_scoring import blocking_diagnostics
    graph=graph_class(packet,report)
    program=report.get('program',{});defs={d['id']:d for d in program.get('definitions',[])}
    primary={d['doc_id'] for d in packet.get('primary_documents',[])}
    target_ids={did for did,d in defs.items() if d.get('kind') in ('ProcedureDef','QueryDef') and any(s.get('doc_id') in primary for s in d.get('source_spans',[]))}
    calls=[c for c in program.get('calls',[]) if c.get('definition_id') in target_ids]
    rows=[]
    for required in contract['required_exports']:
        matching=[]
        for call in calls:
            vid=evidence._returns(call).get(required['label'])
            if not vid:continue
            value=graph.values.get(vid,{})
            valid=(value.get('unit')==required['unit'] and vid in execution.get('values',{}) and graph.root(vid) is not None and evidence._has_input(graph,vid,contract['root']))
            matching.append({'call_id':call.get('id'),'value_id':vid,'producer':value.get('producer'),'port':value.get('output_port'),'passed':valid})
        rows.append({'required':required,'observed':matching,'passed':sum(bool(x['passed']) for x in matching)>=required.get('instances',1)})
    # Input arguments and every bound formal must actually exist and execute.
    missing_bindings=[]
    for call in program.get('calls',[]):
        for name,vid in call.get('formal_bindings',{}).items():
            if not isinstance(vid,str) or graph.root(vid) is None or vid not in execution.get('values',{}):missing_bindings.append({'call_id':call.get('id'),'formal':name,'value_id':vid})
    syntax=report.get('syntax',{});nodes={n['id']:n for n in syntax.get('nodes',[])}
    holes=[n for n in nodes.values() if n.get('kind') in ('Hole','Ambiguous') and any(s.get('doc_id') in primary for s in n.get('source_spans',[]))]
    linked=program.get('linked',{});needed=set();pending=[n for body in linked.get('bodies',{}).values() for n in body]
    while pending:
        nid=pending.pop()
        if nid in needed:continue
        needed.add(nid);node=nodes.get(nid,{})
        pending.extend(node.get('children',[]));pending.extend(v for v in node.get('slots',{}).values() if isinstance(v,str) and v in nodes)
    relevant=[];excluded=[]
    for diagnostic in blocking_diagnostics({'diagnostics':program.get('diagnostics',[])}):
        if diagnostic.get('node_id') in needed or diagnostic.get('doc_id') in primary or not diagnostic.get('node_id'):relevant.append(diagnostic)
        else:excluded.append(diagnostic)
    execution_errors=graph.execution_errors(execution)
    invalid_methods=[e['id'] for e in graph.events.values() if e.get('kind')=='method_call' and not evidence._method_valid(graph,e,execution)]
    checks={'observed_execution_complete':not execution_errors,'method_calls_valid':not invalid_methods,'all_registered_obligations':score['all_obligations_passed'],'target_exports':bool(rows) and all(r['passed'] for r in rows),
        'no_parser_blockers':not score['blocking_diagnostics'],'no_execution_unresolved':not execution.get('unresolved'),
        'real_bindings':not missing_bindings,'primary_ast_complete':not holes,'valid_observed_graph':not graph.source_errors,
        'target_calls_exist':bool(calls),'program_diagnostics_clear':not relevant and not blocking_diagnostics({'diagnostics':linked.get('diagnostics',[])})}
    return {'full_chain_passed':all(checks.values()),'checks':checks,'target_export_evidence':rows,'missing_bindings':missing_bindings,'primary_holes':holes,
        'relevant_program_diagnostics':relevant,'unused_context_diagnostics':excluded,'execution_errors':execution_errors,'invalid_method_calls':invalid_methods}
