import test from "node:test";
import assert from "node:assert/strict";

import {
  DRAFT_SCHEMA,
  createDraftState,
  draftStorageKey,
  exportDrafts,
  importDrafts,
  loadDrafts,
  makeSourceAnchor,
  retractDraft,
  saveDrafts,
  selectOption,
  upsertDraft,
  validateDraftState,
} from "../src/js/scholar-sandbox-drafts.mjs";

function snapshot(overrides = {}) {
  return {
    schema: "ScholarSandboxSnapshot/1",
    snapshot_id: "sifen-38-immutable",
    source: {
      doc_id: "sifen:38",
      reading_id: "default",
      text: "甲😀é乙",
      text_sha256: "source-sha",
      source_id: "sifen",
      unit_id: "sifen:section:38",
    },
    questions: [
      { id: "choice", options: [
        { id: "yes", label: "Yes", action: "choose", payload: { answer: true } },
        { id: "attach", label: "Attach", action: "attach_context", payload: { ignored: true } },
      ] },
    ],
    renderer: { objects: { term_a: { label: "A" } }, facets: [{ facet_key: "definition" }] },
    context_catalog: [{ id: "ctx-1", source_id: "sifen", unit_id: "sifen:section:39", label: "Context", document: { doc_id: "sifen:39" } }],
    ...overrides,
  };
}

function optionRecord(source, id = "draft-1") {
  return {
    id,
    kind: "option",
    status: "draft",
    question_id: "choice",
    option_id: "yes",
    object_id: "term_a",
    facet_key: "definition",
    anchor: makeSourceAnchor(source, 1, 3),
    inputs: { note: "needs checking" },
    reason: "local reading",
  };
}

class MemoryStorage {
  #items = new Map();
  getItem(key) { return this.#items.has(key) ? this.#items.get(key) : null; }
  setItem(key, value) { this.#items.set(key, value); }
}

test("selecting and editing drafts never changes the snapshot", () => {
  const source = snapshot();
  const before = structuredClone(source);
  const selected = selectOption(source, createDraftState(source), "choice", "yes");
  const saved = upsertDraft(source, selected, optionRecord(source));
  const edited = upsertDraft(source, saved, { ...optionRecord(source), reason: "edited locally" });

  assert.equal(edited.schema, DRAFT_SCHEMA);
  assert.equal(edited.selected_options.choice, "yes");
  assert.equal(edited.decisions[0].reason, "edited locally");
  assert.deepEqual(source, before);
  assert.equal(source.questions[0].options[0].payload.answer, true);
});

test("a missing draft id receives a UUID without supplying option payload", () => {
  const source = snapshot();
  const record = optionRecord(source);
  delete record.id;
  const state = upsertDraft(source, createDraftState(source), record);
  assert.match(state.decisions[0].id, /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
  assert.equal(Object.hasOwn(state.decisions[0], "payload"), false);
});

test("source anchors use exact Unicode code-point offsets", () => {
  const source = snapshot();
  assert.deepEqual(makeSourceAnchor(source, 1, 3), {
    doc_id: "sifen:38", reading_id: "default", source_sha256: "source-sha",
    start: 1, end: 3, quote: "😀e", offset_unit: "unicode_code_point",
  });
  assert.deepEqual(makeSourceAnchor(source, 3, 5), {
    doc_id: "sifen:38", reading_id: "default", source_sha256: "source-sha",
    start: 3, end: 5, quote: "́乙", offset_unit: "unicode_code_point",
  });
  assert.throws(() => validateDraftState(source, {
    ...createDraftState(source),
    decisions: [{ ...optionRecord(source), anchor: {
      ...makeSourceAnchor(source, 1, 3), quote: "😀",
    } }],
  }), /exactly match/);
  assert.throws(() => validateDraftState(source, {
    ...createDraftState(source),
    decisions: [{ ...optionRecord(source), anchor: {
      ...makeSourceAnchor(source, 1, 3), source_sha256: "another-source",
    } }],
  }), /source_sha256/);
  assert.throws(() => validateDraftState(source, {
    ...createDraftState(source),
    decisions: [{ ...optionRecord(source), anchor: {
      ...makeSourceAnchor(source, 1, 3), offset_unit: "utf16_code_unit",
    } }],
  }), /offset_unit/);
  assert.throws(() => makeSourceAnchor(source, 1, 6), /outside/);
});

test("imports are identity-bound and failure leaves existing persisted drafts intact", () => {
  const source = snapshot();
  const storage = new MemoryStorage();
  const saved = saveDrafts(source, upsertDraft(source, createDraftState(source), optionRecord(source)), storage);
  const mismatched = { ...saved, snapshot_id: "another-snapshot" };

  assert.throws(() => importDrafts(source, JSON.stringify(mismatched)), /snapshot_id/);
  assert.throws(() => importDrafts(source, "{not JSON"), /valid JSON/);
  assert.deepEqual(loadDrafts(source, storage), saved);
});

test("context drafts require a known catalog item and attach_context option", () => {
  const source = snapshot();
  const base = createDraftState(source);
  const context = {
    id: "context-1", kind: "context", status: "draft", question_id: "choice", option_id: "attach",
    context_id: "ctx-1", anchor: makeSourceAnchor(source, 0, 1), inputs: {}, reason: "compare unit",
  };
  assert.equal(upsertDraft(source, base, context).decisions[0].context_id, "ctx-1");
  assert.throws(() => upsertDraft(source, base, { ...context, context_id: "unknown" }), /context_id is unknown/);
  assert.throws(() => upsertDraft(source, base, { ...context, option_id: "yes" }), /attach_context/);
});

test("unsafe keys and forged reviewed state are rejected", () => {
  const source = snapshot();
  const draft = optionRecord(source);
  const unsafeInputs = JSON.parse('{"__proto__":{"polluted":true}}');
  assert.throws(() => upsertDraft(source, createDraftState(source), { ...draft, inputs: unsafeInputs }), /unsafe key/);
  assert.throws(() => upsertDraft(source, createDraftState(source), { ...draft, status: "reviewed" }), /must be draft/);
  assert.throws(() => upsertDraft(source, createDraftState(source), { ...draft, reviewed: true }), /unsupported field/);
  assert.throws(() => importDrafts(source, JSON.stringify({ ...createDraftState(source), reviewed: true })), /unsupported field/);
});

test("retract, export/import, and storage preserve a safe independent state", () => {
  const source = snapshot();
  const storage = new MemoryStorage();
  const first = upsertDraft(source, createDraftState(source), optionRecord(source, "one"));
  const boundary = {
    id: "two", kind: "term_boundary", status: "draft", object_id: "term_a",
    anchor: makeSourceAnchor(source, 3, 5), inputs: { boundary: "candidate" }, reason: "local span",
  };
  const normalized = upsertDraft(source, first, boundary);
  const restored = importDrafts(source, exportDrafts(source, normalized));
  const retracted = retractDraft(source, restored, "one");

  assert.equal(retracted.decisions.length, 1);
  assert.equal(retracted.decisions[0].kind, "term_boundary");
  assert.equal(draftStorageKey(source), "scholar-sandbox-drafts:sifen-38-immutable");
  assert.deepEqual(loadDrafts(source, storage), createDraftState(source));
  assert.deepEqual(saveDrafts(source, retracted, storage), retracted);
  assert.deepEqual(loadDrafts(source, storage), retracted);
});

test("corrupt stored data is surfaced instead of silently erased", () => {
  const source = snapshot();
  const storage = new MemoryStorage();
  storage.setItem(draftStorageKey(source), "not JSON");
  assert.throws(() => loadDrafts(source, storage), /valid JSON/);
});
