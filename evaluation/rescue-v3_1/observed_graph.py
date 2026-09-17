"""Read-only graph view of reported, explicitly instantiated method bodies.

This does not compile a method or create an expected graph. It validates the
parser's actual body instances against its definition and resolves reported
return bindings. Invalid projections are rejected, never reconstructed.
"""
import copy
import importlib.util
from pathlib import Path
_spec=importlib.util.spec_from_file_location('rescue_legacy_graph',Path(__file__).resolve().parents[1]/'handoff-v3/civil_contracts.py')
_old=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_old)

class Graph(_old.Graph):
    def __init__(self,packet,report):
        # Validate occurrences before any ID-indexed projection can erase them.
        identity_errors=[];invalid_ids=set()
        for field,items in [('events',report.get('events',[])),('value_instances',report.get('value_instances',report.get('values',[]))),('method_library',report.get('method_library',[])),('method_instances',report.get('method_instances',[])),('definitions',report.get('program',{}).get('definitions',[])),('calls',report.get('program',{}).get('calls',[]))]:
            key='call_event_id' if field=='method_instances' else 'id'
            seen=set()
            for item in items:
                identity=item.get(key)
                if not isinstance(identity,str) or not identity or identity in seen:
                    identity_errors.append({'cause':'duplicate_or_invalid_identity','container':field,'identity':identity})
                    if field in ('events','value_instances'):invalid_ids.add(identity)
                seen.add(identity)
        safe=copy.deepcopy(report)
        safe['events']=[e for e in report.get('events',[]) if e.get('id') not in invalid_ids]
        safe['value_instances']=[v for v in report.get('value_instances',report.get('values',[])) if v.get('id') not in invalid_ids]
        super().__init__(packet,safe)
        self.report=report
        self.source_errors.extend(identity_errors)
        self.identity_errors=identity_errors
        self.main_event_ids=set(self.events);self.return_links={};self.call_sites={};self.enclosing_calls={}
        self.commutative_alignments={}
        reserved_values={v.get('id') for v in report.get('value_instances',report.get('values',[])) if isinstance(v.get('id'),str)}
        for instance in report.get('method_instances',[]):
            # Validate the complete collection before projecting any local value.
            # Extras must not replace global/prior identities or create records
            # that no write of this instance actually owns.
            nodes=instance.get('events',[]);vals=instance.get('value_instances',[])
            identifiers=[v.get('id') for v in vals]
            body_writes=[(vid,node.get('id'),port) for node in nodes for port,vid in node.get('writes',{}).items()]
            identifiers_valid=all(isinstance(vid,str) and vid for vid in identifiers)
            writes_valid=all(isinstance(vid,str) and vid for vid,_,_ in body_writes)
            owned=(identifiers_valid and writes_valid and len(set(identifiers))==len(identifiers) and
                   len({vid for vid,_,_ in body_writes})==len(body_writes) and
                   set(identifiers)=={vid for vid,_,_ in body_writes} and not set(identifiers)&reserved_values)
            reserved_values.update(vid for vid in identifiers if isinstance(vid,str))
            if owned:
                producers={vid:(producer,port) for vid,producer,port in body_writes}
                owned=all((v.get('producer'),v.get('output_port'))==producers[v['id']] for v in vals)
            if not owned:
                error={'cause':'invalid_method_instance_value_ownership','call_event_id':instance.get('call_event_id')}
                self.identity_errors.append(error);self.source_errors.append(error)
                continue
            outer=self.events.get(instance.get('call_event_id'),{})
            methods=[m for m in report.get('method_library',[]) if m.get('id')==instance.get('definition_id')]
            if outer.get('kind')!='method_call' or len(methods)!=1:
                self.source_errors.append({'cause':'invalid_method_instance_target'});continue
            method=methods[0];binding=outer.get('method_binding',{})
            nodes=instance.get('events',[]);vals=instance.get('value_instances',[])
            local={'$'+k:v for k,v in instance.get('formal_bindings',{}).items()}
            valid=(instance.get('formal_bindings')==binding.get('formal_actuals',binding.get('actuals')) and method.get('id')==outer.get('attributes',{}).get('target') and len(nodes)==len(method.get('body',[])) and instance.get('call_spans')==outer.get('source_spans'))
            value_map={v.get('id'):v for v in vals};node_ids=set()
            valid=valid and len(value_map)==len(vals) and None not in value_map
            for declared,node in zip(method.get('body',[]),nodes):
                if node.get('id') in self.events or node.get('id') in node_ids:valid=False
                node_ids.add(node.get('id'))
                wanted={port:local.get(vid) for port,vid in declared.get('reads',{}).items()}
                valid=valid and None not in wanted.values() and node.get('reads')==wanted and node.get('kind')==declared.get('kind') and node.get('attributes',{})==declared.get('attributes',{}) and node.get('source_spans')==declared.get('source_spans')
                valid=valid and set(node.get('writes',{}))==set(declared.get('writes',{}))
                for port,name in declared.get('writes',{}).items():
                    vid=node.get('writes',{}).get(port);v=value_map.get(vid,{})
                    valid=valid and vid not in self.values and v.get('producer')==node.get('id') and v.get('output_port')==port
                    local[name]=vid
            expected_returns={outer.get('writes',{}).get(port):local.get(name) for port,name in method.get('returns',{}).items()}
            valid=valid and None not in expected_returns and None not in expected_returns.values() and instance.get('return_bindings')==expected_returns and binding.get('return_bindings')==expected_returns
            valid=valid and all(self.valid_span(s) for n in nodes for s in n.get('source_spans',[]))
            if not valid:
                self.source_errors.append({'cause':'invalid_method_instance_projection','call_event_id':outer.get('id')});continue
            for node in nodes:
                self.events[node['id']]=copy.deepcopy(node)
                self.call_sites[node['id']]=instance['call_spans']
                self.enclosing_calls[node['id']]=outer.get('call_id',outer.get('scope',{}).get('call_id'))
            self.values.update(value_map);self.return_links.update(expected_returns)

    def root(self,vid):
        seen=set()
        while isinstance(vid,str) and vid in self.values and vid not in seen:
            seen.add(vid);value=self.values[vid];event=self.events.get(value.get('producer'),{})
            if event.get('writes',{}).get(value.get('output_port'))!=vid:return None
            target=self.return_links.get(vid)
            if target is None and event.get('kind') in ('alias','load') and value.get('output_port')=='result':target=event.get('reads',{}).get('value')
            if target is not None:
                source=self.values.get(target,{})
                for field in ('unit','time_frame'):
                    a,b=value.get(field),source.get(field)
                    if a not in (None,'unknown','opaque') and b not in (None,'unknown','opaque') and a!=b:return None
                vid=target;continue
            return vid
        return None

    def at(self,event,anchor):
        if super().at(event,anchor):return True
        return super().at({'source_spans':self.call_sites.get(event.get('id'),[])},anchor)

    def align(self,event,predicate):
        """Choose one consistent whole-event permutation, never per-atom swaps."""
        if event.get('kind') not in ('add','multiply') or not {'left','right'}<=set(predicate.get('reads',{})) or not {'left','right'}<=set(event.get('reads',{})):return event
        def score(reads):return sum(self.value(reads.get(k),v) for k,v in predicate['reads'].items())
        original=event['reads'];swapped=dict(original,left=original['right'],right=original['left'])
        if score(swapped)<=score(original):return event
        self.commutative_alignments[event['id']]={'left':'right','right':'left'}
        return dict(event,reads=swapped)

    def event(self,event,predicate,active=None):
        return super().event(self.align(event,predicate),predicate,active)

    def execution_errors(self,execution):
        """Require one concrete executor step for every value-producing event."""
        errors=[];values=execution.get('values',{});results=execution.get('event_results',{})
        for eid in self.main_event_ids:
            event=self.events[eid]
            if not event.get('writes'):continue
            steps=[s for s in execution.get('execution_trace',[]) if s.get('event_id')==eid and 'kind' in s]
            if len(steps)!=1:
                errors.append({'event_id':eid,'cause':'missing_or_duplicate_execution_step'});continue
            step=steps[0];reads=event.get('reads',{});writes=event.get('writes',{})
            valid=(step.get('kind')==event.get('kind') and all(v in values for v in reads.values()) and
                step.get('reads')=={k:values.get(v) for k,v in reads.items()} and
                eid in results and step.get('writes')==results[eid] and
                all(k in step.get('writes',{}) and v in values and values[v]==step['writes'][k] for k,v in writes.items()))
            if not valid:errors.append({'event_id':eid,'cause':'execution_identity_mismatch'})
        return errors
