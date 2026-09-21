"""Deterministic, read-only export for the public Scholar Sandbox.

The snapshot deliberately consumes the current reviewed response and its
existing presentation projections.  It neither records a decision nor creates
an alternative parser, compiler, Kernel, or corpus interpretation path.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from html import unescape
from pathlib import Path
import re

from analysis_parser.ontology import entry
from adjudication.anchors import anchor_for
from source_adapters import corpus_index, corpus_review
from tools.parser_inspector.segmentation_review import _type_badge, _type_style
from tools.parser_inspector.review_panel import composition_choices, question_options
from workbench import service
from workbench.annotation_projection import project_scholar_source
from workbench.procedure_model import build_procedure_model
from workbench.scholar_renderer import build_renderer_model, selection_details


SCHEMA = "ScholarSandboxSnapshot/1"
DEFAULT_JOB_ID = "scholar-renderer-correction-20260920"
DEFAULT_OUTPUT = Path("static/data/inspector/sifen-38.snapshot.json")


def canonical_json(value):
    """Return the stable UTF-8 JSON representation used by the public file."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def _sha256(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _object_label(row):
    """Reuse the current scholar object fields; this adds no semantic label."""
    if row.get("surface"):
        return row["surface"]
    if row.get("formal"):
        return row["formal"]
    if row.get("operation"):
        return entry("operation", row["operation"]).get("label_en", row["operation"])
    presentation = row.get("presentation") or {}
    if isinstance(presentation, dict) and presentation.get("label"):
        return presentation["label"]
    return row["id"]


def _unit_type_labels():
    """Export the existing corpus-browser presentation, rather than a new map."""
    result = {}
    for code in corpus_index.UNIT_TYPES:
        badge = _type_badge(code)
        result[code] = {"label": unescape(re.sub(r"<[^>]+>", "", badge)), "style": _type_style(code)}
    return result


def _context_label(unit):
    """The existing corpus-browser identity in a portable plain-text form."""
    sections = ",".join(map(str, unit["sections"]))
    text = unit["text_original"].strip()
    end = re.search(r"[，。；：！？.!?;:\r\n]", text)
    preview = text[:end.start()].rstrip() if end else text
    return f"§{sections} · {preview} · {unit['source_spans'][0]['start']}"


def _port_labels(model):
    roles = set()
    for step in model["steps"]:
        roles.update(item.get("role") for item in step.get("inputs", []) if item.get("role"))
        roles.update(item.get("port") for item in step.get("outputs", []) if item.get("port"))
    for facet in model["facets"]:
        if facet.get("role"):
            roles.add(facet["role"])
    return {code: entry("port", code).get("label_en", code) for code in sorted(roles)}


def _source(document):
    return {key: deepcopy(document[key]) for key in ("doc_id", "reading_id", "text", "text_sha256")}


def _available_corpora(root):
    """Copy existing segmentation workspaces without recalculating them."""
    root = Path(root)
    result, contexts = [], []
    for registered in corpus_index.list_review_sources(root):
        source_id = registered["id"]
        auto_path, overrides_path, effective_path = corpus_review.paths(root, source_id)
        manifest_path = corpus_review.workspace(root, source_id) / "manifest.json"
        if not all(path.is_file() for path in (auto_path, overrides_path, effective_path, manifest_path)):
            continue
        # _load is intentionally used here rather than the locking public helper:
        # the export must be a no-write read of an already generated workspace.
        state = corpus_review._load(root, source_id)
        if state["stale"]:
            continue
        effective = deepcopy(state["effective"]["units"])
        result.append({
            "id": source_id,
            "label": corpus_index.review_source_display_label(registered),
            "source_identity": deepcopy(state["effective"].get("source", {})),
            "auto": deepcopy(state["auto"]["units"]),
            "effective": effective,
            "review_status": deepcopy(state["manifest"].get("review_status", {})),
            "history": deepcopy(state["overrides"].get("history", [])),
        })
        for unit in effective:
            document = service.review_context_document(root, source_id, unit["id"])
            contexts.append({
                "id": source_id + ":" + unit["id"],
                "source_id": source_id,
                "unit_id": unit["id"],
                "label": corpus_index.review_source_display_label(registered) + " · " + _context_label(unit),
                "document": document,
            })
    return result, contexts


def build_snapshot(root=".", job_id=DEFAULT_JOB_ID):
    """Build a read-only ScholarSandboxSnapshot/1 from one current ReviewJob."""
    root = Path(root).resolve()
    response = service.compile_review_job(root, job_id)
    if response.get("freshness", {}).get("status") != "current":
        raise ValueError("sandbox_snapshot_requires_current_review_job")
    projection = project_scholar_source(
        response["effective_packet"], response["compilation"], response["questions"],
        response["session"]["decisions"], response["compilation"]["replay"]["decision_status"],
    )
    renderer = build_renderer_model(response["effective_packet"], projection, response["questions"], root=root)
    procedure_model = build_procedure_model(projection)
    questions = [{**deepcopy(question), "options": deepcopy(question_options(question))}
                 for question in response["questions"]]
    object_details = {object_id: selection_details(renderer, object_id, root=root)
                      for object_id in sorted(renderer["objects"])}
    facet_details = {facet["facet_key"]: selection_details(renderer, facet["object_id"], facet["facet_key"], root=root)
                     for facet in sorted(renderer["facets"], key=lambda row: row["facet_key"])}
    corpora, context_catalog = _available_corpora(root)
    job = response["job"]
    source_document = next(document for document in response["effective_packet"]["primary_documents"]
                           if document["doc_id"] == projection["source"]["doc_id"])
    source_anchor = anchor_for(response["effective_packet"], source_document["doc_id"], 0,
                               len(source_document["text"]), source_document["reading_id"])
    snapshot = {
        "schema": SCHEMA,
        "source": {
            **_source(projection["source"]),
            "source_id": source_document["source"]["source_id"],
            "unit_id": source_document["source"]["unit_id"],
            "anchor": source_anchor,
            "source_provenance": deepcopy(source_document["source"]),
        },
        "provenance": {
            "review_job_id": job["job_id"], "revision": job["revision"], "branch_id": job["branch_id"],
            "job_digest": response["job_digest"], "source_selection": deepcopy(job["source_selection"]),
            "base_packet_identity": deepcopy(job["base_packet_identity"]),
            "analysis_inputs_digest": job["analysis_inputs_digest"],
            "identity_locks": deepcopy(job["session"]["identity_locks"]),
        },
        "projection": projection,
        "renderer": renderer,
        "questions": questions,
        "review": {
            "decisions": deepcopy(response["session"]["decisions"]),
            "status": deepcopy(response["compilation"]["replay"]["decision_status"]),
            "history": deepcopy(response["session"]["decisions"]),
            "management_events": deepcopy(job["management_events"]),
            "managed_scope": deepcopy(response["managed_scope"]),
            "summary": deepcopy(response["summary"]),
        },
        "procedure_model": procedure_model,
        "details": {"objects": object_details, "facets": facet_details},
        "labels": {
            "objects": {ident: _object_label(row) for ident, row in sorted(renderer["objects"].items())},
            "roles": _port_labels(renderer),
            "unit_types": _unit_type_labels(),
        },
        "context_catalog": context_catalog,
        "corpora": corpora,
        "presentation_registry": {
            "compose_by_question": {
                question["id"]: composition_choices(question)
                for question in response["questions"] if question["kind"] == "term_interpretation"
            },
        },
    }
    snapshot["snapshot_id"] = _sha256(snapshot)
    return snapshot


def serialize_snapshot(snapshot):
    if snapshot.get("schema") != SCHEMA:
        raise ValueError("sandbox_snapshot_serializer_requires_v1")
    snapshot_id = snapshot.get("snapshot_id")
    unsigned = {key: deepcopy(value) for key, value in snapshot.items() if key != "snapshot_id"}
    if snapshot_id != _sha256(unsigned):
        raise ValueError("sandbox_snapshot_id_mismatch")
    return canonical_json(snapshot)


def export_snapshot(snapshot, output):
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(serialize_snapshot(snapshot), encoding="utf-8", newline="\n")
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description="Export the static Scholar Sandbox snapshot.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--job-id", default=DEFAULT_JOB_ID)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    snapshot = build_snapshot(args.root, args.job_id)
    output = export_snapshot(snapshot, Path(args.root) / args.output)
    print(output)


if __name__ == "__main__":
    main()
