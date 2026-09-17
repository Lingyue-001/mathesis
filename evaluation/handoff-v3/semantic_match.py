"""Parser-independent, policy-driven semantic obligation matching."""
from copy import deepcopy
from itertools import permutations

LAYERS = ("source_identity", "producer_port", "scope_control", "method_call", "scale_rate")
ISSUES = {"parser_error":"parser_error", "parser_gap":"parser_error", "unresolved_parser":"parser_error",
          "missing_context":"missing_context", "missing_external_data":"missing_context", "requires_external_data":"missing_context",
          "text_ambiguity":"text_ambiguity", "textual_ambiguity":"text_ambiguity", "interpretive_ambiguity":"text_ambiguity"}

def _metric(): return {"TP":0,"FP":0,"FN":0,"precision":None,"recall":None}
def _finish(m):
    p,r=m["TP"]+m["FP"],m["TP"]+m["FN"]
    m["precision"]=m["TP"]/p if p else None; m["recall"]=m["TP"]/r if r else None

def _docs(report):
    return {(d.get("doc_id"),d.get("reading_id")):d.get("text_sha256",d.get("reading_hash"))
            for d in report.get("source_documents",report.get("documents",[]))}
def _span(s, hashes):
    h=s.get("text_sha256") or s.get("reading_hash") or hashes.get((s.get("doc_id"),s.get("reading_id")))
    return s.get("doc_id"),s.get("reading_id"),h,s.get("start"),s.get("end")
def _values(report):
    vals={v["id"]:deepcopy(v) for v in report.get("values",report.get("value_instances",[]))}
    for e in report.get("events",[]):
        if e.get("kind") not in ("alias","load"): continue
        src,dst=e.get("reads",{}).get("value"),e.get("writes",{}).get("result"); out=vals.get(dst,{})
        if src in vals and out.get("producer")==e.get("id") and out.get("output_port")=="result":
            out["transparent_alias"],out["alias_of"]=True,src
    return vals
def _origin(vid, vals):
    seen=set()
    while vid in vals and vid not in seen:
        seen.add(vid); v=vals[vid]
        if not v.get("transparent_alias") or v.get("alias_of") not in vals: break
        vid=v["alias_of"]
    return vid
def _valid_value(vid, vals, by_id):
    v=vals[vid]; producer,port=v.get("producer"),v.get("output_port")
    if producer is None or port is None: return producer is None and port is None
    return producer in by_id and by_id[producer].get("writes",{}).get(port)==vid
def _selected_id(selector, vals):
    if isinstance(selector,dict) and set(selector)=={"value_id"}: return selector["value_id"] if selector["value_id"] in vals else None
    if isinstance(selector,str):
        matches=[vid for vid,v in vals.items() if v.get("semantic_id") is not None and v.get("semantic_id")==selector]
        return matches[0] if len(matches)==1 else None
    return None
def _endpoint(actual, selector, event, port, direction, vals, by_id, hashes):
    root=_origin(actual,vals)
    if root not in vals or not _valid_value(root,vals,by_id): return False
    v=vals[root]
    if direction=="writes" and (v.get("producer"),v.get("output_port"))!=(event.get("id"),port): return False
    selected=_selected_id(selector,vals)
    if selected is not None or not isinstance(selector,dict): return selected==root
    desc=selector.get("origin")
    if not isinstance(desc,dict): return False
    producer=by_id.get(v.get("producer"))
    return bool(producer and v.get("output_port")==desc.get("port") and producer.get("kind")==desc.get("kind")
                and desc.get("anchor") and any(_span(s,hashes)==_span(desc["anchor"],hashes) for s in producer.get("source_spans",[])))
def _relation(event,direction,expected,m,vals,by_id,hashes):
    actual=event.get(direction,{}); clean=True
    for port in sorted(set(actual)|set(expected)):
        ok=port in actual and port in expected and _endpoint(actual[port],expected[port],event,port,direction,vals,by_id,hashes)
        if ok: m["TP"]+=1
        else:
            clean=False
            if port in actual:m["FP"]+=1
            if port in expected:m["FN"]+=1
    return clean
def _object(actual,expected,m):
    if actual==expected:m["TP"]+=1; return True
    if actual is not None:m["FP"]+=1
    m["FN"]+=1; return False
def _nested(x,vals):
    if isinstance(x,dict):return {k:_nested(v,vals) for k,v in x.items()}
    if isinstance(x,list):return [_nested(v,vals) for v in x]
    if x in vals:
        root=_origin(x,vals); return vals[root].get("semantic_id") if vals[root].get("semantic_id") is not None else root
    return x
def _score_event(event,pred,vals,by_id,hashes):
    layers={n:_metric() for n in LAYERS}; clean=_object(event.get("kind"),pred.get("kind"),layers["source_identity"])
    for d in ("reads","writes"):
        if d in pred:clean=_relation(event,d,pred[d],layers["producer_port"],vals,by_id,hashes) and clean
    if "scope" in pred:clean=_object({k:event.get("scope",{}).get(k) for k in pred["scope"]},pred["scope"],layers["scope_control"]) and clean
    for field,layer in (("control","scope_control"),("method_binding","method_call"),("quantity","scale_rate")):
        if field in pred:clean=_object(_nested(event.get(field,event.get("attributes",{}).get(field)),vals),pred[field],layers[layer]) and clean
    return clean,layers
def _best(candidates,preds,vals,by_id,hashes):
    if len(candidates)<len(preds):return None
    options=[]
    for chosen in permutations(sorted(candidates,key=lambda e:str(e.get("id"))),len(preds)):
        scored=[_score_event(e,p,vals,by_id,hashes) for e,p in zip(chosen,preds)]
        fpfn=sum(l[k] for _,ls in scored for l in ls.values() for k in ("FP","FN")); tp=sum(l["TP"] for _,ls in scored for l in ls.values())
        options.append(((fpfn,-tp,tuple(str(e.get("id")) for e in chosen)),chosen,scored))
    return min(options,key=lambda x:x[0])[1:]
def _unresolved(report,key,hashes):
    for issue in report.get("unresolved",[]):
        if any(_span(s,hashes)==key for s in issue.get("source_spans",[])):return ISSUES.get(issue.get("cause"))
def _coverage(report,reference):
    c=report.get("coverage") if isinstance(report.get("coverage"),dict) else {}
    raw_diagnostics=report.get("diagnostics",[])
    diagnostic_items=raw_diagnostics if isinstance(raw_diagnostics,list) else []
    d=raw_diagnostics if isinstance(raw_diagnostics,dict) else {}
    diagnostic_causes=[item.get("cause") for item in diagnostic_items if isinstance(item,dict)]
    diagnostic_spans=[span for item in diagnostic_items if isinstance(item,dict) for span in item.get("source_spans",[])]
    unparsed=list(report.get("unparsed_spans",[]))+list(c.get("unparsed_spans",[]))+list(d.get("unparsed_spans",[])); unscored=c.get("unscored_ranges",report.get("unscored_ranges",[]))
    complete=reference.get("coverage") in ("complete","full",True)
    out={"reference_domain":reference.get("coverage","unspecified"),"audited_obligations":len(reference.get("obligations",[])),
         "total_source_length":c.get("total_source_length",report.get("total_source_length")),"audited_ranges":c.get("audited_ranges",report.get("audited_ranges",[])),
         "unscored_ranges":unscored,"unscored_domain":unscored if unscored else (0 if complete else "present_or_unspecified"),
         "unparsed_spans":unparsed,"unparsed_span_count":len(unparsed),"unresolved_count":len(report.get("unresolved",[])),
         "diagnostic_count":len(diagnostic_items),"diagnostic_causes":diagnostic_causes,"diagnostic_spans":diagnostic_spans}
    blocking_causes={"parser_error","parser_gap","unresolved_parser","unknown_domain","unparsed","unparsed_span"}
    blocked=bool(unparsed or unscored or report.get("parser_error") or report.get("unresolved") or d.get("parser_error") or d.get("unknown_domain") or d.get("unresolved") or blocking_causes.intersection(diagnostic_causes))
    return out,blocked

def evaluate_obligations(report:dict,reference:dict,policy:dict)->dict:
    """Match exact-occurrence obligations using explicit event predicates."""
    layers={n:_metric() for n in LAYERS}; hashes=_docs(report); vals=_values(report); events=report.get("events",[]); by_id={e.get("id"):e for e in events}
    supported=set(policy.get("supported_actions",[])); rows=[]; unsupported=False
    for obligation in reference.get("obligations",[]):
        oid=obligation["id"]; entry=policy.get("obligations",{}).get(oid,obligation.get("predicate")); preds=entry.get("events") if isinstance(entry,dict) and "events" in entry else [entry]
        if not preds or any(not isinstance(p,dict) or p.get("kind") not in supported for p in preds):
            unsupported=True; rows.append({"id":oid,"status":"evaluator_unsupported","matched_event_ids":[],"scores":None}); continue
        key=_span(obligation["anchor"],hashes); candidates=[e for e in events if any(_span(s,hashes)==key for s in e.get("source_spans",[]))]
        known=[e for e in candidates if e.get("kind") in supported]; unknown=[e for e in candidates if e.get("kind") not in supported]
        if candidates and not known:
            unsupported=True; rows.append({"id":oid,"status":"evaluator_unsupported","matched_event_ids":[],"scores":None,"actual_kinds":sorted({e.get('kind') for e in candidates})}); continue
        if not candidates:
            status=_unresolved(report,key,hashes) or "missing"; layers["source_identity"]["FN"]+=1
            rows.append({"id":oid,"status":status,"matched_event_ids":[],"scores":{"TP":0,"FP":0,"FN":1}}); continue
        realized=_best(known,preds,vals,by_id,hashes)
        if unknown and (realized is None or not all(ok for ok,_ in realized[1])):
            unsupported=True; rows.append({"id":oid,"status":"evaluator_unsupported","matched_event_ids":[],"scores":None,"actual_kinds":sorted({e.get('kind') for e in unknown})}); continue
        if realized is None:
            missing=len(preds)-len(known); layers["source_identity"]["FN"]+=missing
            rows.append({"id":oid,"status":"fail","matched_event_ids":[],"scores":{"TP":0,"FP":0,"FN":missing}}); continue
        chosen,scored=realized; row_layers={n:{"TP":0,"FP":0,"FN":0} for n in LAYERS}
        for _,ls in scored:
            for n in LAYERS:
                for k in ("TP","FP","FN"):layers[n][k]+=ls[n][k]; row_layers[n][k]+=ls[n][k]
        score={k:sum(m[k] for m in row_layers.values()) for k in ("TP","FP","FN")}
        rows.append({"id":oid,"status":"pass" if all(ok for ok,_ in scored) else "fail","matched_event_ids":[e.get("id") for e in chosen],"scores":score,"layers":row_layers})
    for m in layers.values():_finish(m)
    coverage,blocked=_coverage(report,reference); statuses=[r["status"] for r in rows]; complete=reference.get("coverage") in ("complete","full",True)
    full=None if unsupported else bool(rows) and all(s=="pass" for s in statuses) and complete and not blocked
    return {"obligations":rows,"layers":layers,"full_chain_passed":full,"coverage":coverage,"supported_actions":sorted(supported)}
