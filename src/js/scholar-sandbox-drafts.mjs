/*
 * Static Scholar Sandbox draft store.
 *
 * This module never parses, recompiles, validates, or derives scholarly
 * semantics. A ScholarSandboxSnapshot/1 is immutable input. Drafts are a
 * separately persisted ScholarSandboxDrafts/1 envelope, bound to the
 * snapshot id and the source document/reading/text hash.
 *
 * Public API:
 *   createDraftState(snapshot)
 *   validateDraftState(snapshot, value)
 *   selectOption(snapshot, state, questionId, optionId)
 *   upsertDraft(snapshot, state, record)
 *   retractDraft(snapshot, state, id)
 *   exportDrafts(snapshot, state)
 *   importDrafts(snapshot, text)
 *   draftStorageKey(snapshot)
 *   loadDrafts(snapshot, storage)
 *   saveDrafts(snapshot, state, storage)
 *   makeSourceAnchor(snapshot, start, end)
 *
 * All state-changing functions return a new value. `selectOption` only
 * records an unsaved local choice; a decision becomes persistent draft review
 * only when a caller saves a valid record with `upsertDraft` and storage.
 */

export const SNAPSHOT_SCHEMA = "ScholarSandboxSnapshot/1";
export const DRAFT_SCHEMA = "ScholarSandboxDrafts/1";
export const MAX_IMPORT_BYTES = 5 * 1024 * 1024;

const UNSAFE_KEYS = new Set(["__proto__", "prototype", "constructor"]);
const RECORD_KEYS = new Set([
  "id", "kind", "status", "question_id", "option_id", "object_id",
  "facet_key", "anchor", "context_id", "inputs", "reason",
]);
const ANCHOR_KEYS = new Set([
  "doc_id", "reading_id", "source_sha256", "start", "end", "quote", "offset_unit",
]);
const STATE_KEYS = new Set(["schema", "snapshot_id", "source", "selected_options", "decisions"]);
const DRAFT_SOURCE_KEYS = new Set(["doc_id", "reading_id", "text_sha256"]);

function fail(message) {
  throw new TypeError(`Scholar Sandbox drafts: ${message}`);
}

function isPlainObject(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function assertSafeKey(key, label) {
  if (UNSAFE_KEYS.has(key)) fail(`${label} contains unsafe key ${key}`);
}

function assertSafeJson(value, label) {
  if (value === null || typeof value === "string" || typeof value === "boolean") return;
  if (typeof value === "number") {
    if (!Number.isFinite(value)) fail(`${label} contains a non-finite number`);
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => assertSafeJson(item, `${label}[${index}]`));
    return;
  }
  if (!isPlainObject(value)) fail(`${label} must be JSON data`);
  for (const [key, child] of Object.entries(value)) {
    assertSafeKey(key, label);
    assertSafeJson(child, `${label}.${key}`);
  }
}

function safeCopy(value) {
  assertSafeJson(value, "value");
  if (value === null || typeof value !== "object") return value;
  if (Array.isArray(value)) return value.map(safeCopy);
  const copy = Object.create(null);
  for (const [key, child] of Object.entries(value)) copy[key] = safeCopy(child);
  return copy;
}

function assertString(value, label) {
  if (typeof value !== "string" || value.length === 0) fail(`${label} must be a non-empty string`);
  return value;
}

function assertSafeIdentifier(value, label) {
  assertString(value, label);
  assertSafeKey(value, label);
  return value;
}

function assertOnlyKeys(value, allowed, label) {
  for (const key of Object.keys(value)) {
    assertSafeKey(key, label);
    if (!allowed.has(key)) fail(`${label} contains unsupported field ${key}`);
  }
}

function snapshotSchema(snapshot) {
  return snapshot?.schema ?? snapshot?.format ?? snapshot?.schema_version;
}

function snapshotIndex(snapshot) {
  if (!isPlainObject(snapshot)) fail("snapshot must be an object");
  if (snapshotSchema(snapshot) !== SNAPSHOT_SCHEMA) fail("snapshot schema is not ScholarSandboxSnapshot/1");
  const snapshotId = assertString(snapshot.snapshot_id, "snapshot.snapshot_id");
  const source = snapshot.source;
  if (!isPlainObject(source)) fail("snapshot.source must be an object");
  const identity = {
    doc_id: assertString(source.doc_id, "snapshot.source.doc_id"),
    reading_id: assertString(source.reading_id, "snapshot.source.reading_id"),
    text_sha256: assertString(source.text_sha256, "snapshot.source.text_sha256"),
  };
  assertString(source.text, "snapshot.source.text");
  assertString(source.source_id, "snapshot.source.source_id");
  assertString(source.unit_id, "snapshot.source.unit_id");

  if (!Array.isArray(snapshot.questions)) fail("snapshot.questions must be an array");
  const questions = new Map();
  for (const question of snapshot.questions) {
    if (!isPlainObject(question)) fail("each snapshot question must be an object");
    const questionId = assertSafeIdentifier(question.id, "snapshot question id");
    if (questions.has(questionId)) fail(`duplicate snapshot question ${questionId}`);
    if (!Array.isArray(question.options)) fail(`question ${questionId} options must be an array`);
    const options = new Map();
    for (const option of question.options) {
      if (!isPlainObject(option)) fail(`question ${questionId} has invalid option`);
      const optionId = assertSafeIdentifier(option.id, `option id for ${questionId}`);
      if (options.has(optionId)) fail(`duplicate option ${optionId} for ${questionId}`);
      assertString(option.label, `option label for ${questionId}`);
      assertString(option.action, `option action for ${questionId}`);
      options.set(optionId, option);
    }
    questions.set(questionId, options);
  }

  const renderer = snapshot.renderer;
  if (!isPlainObject(renderer) || !isPlainObject(renderer.objects) || !Array.isArray(renderer.facets)) {
    fail("snapshot.renderer must contain objects and facets");
  }
  const objectIds = new Set();
  for (const objectId of Object.keys(renderer.objects)) {
    assertSafeIdentifier(objectId, "renderer object id");
    objectIds.add(objectId);
  }
  const facetKeys = new Set();
  for (const facet of renderer.facets) {
    const facetKey = typeof facet === "string" ? facet : facet?.facet_key ?? facet?.key ?? facet?.id;
    assertSafeIdentifier(facetKey, "renderer facet key");
    if (facetKeys.has(facetKey)) fail(`duplicate renderer facet ${facetKey}`);
    facetKeys.add(facetKey);
  }

  if (!Array.isArray(snapshot.context_catalog)) fail("snapshot.context_catalog must be an array");
  const contextIds = new Set();
  for (const context of snapshot.context_catalog) {
    if (!isPlainObject(context)) fail("each context catalog entry must be an object");
    const contextId = assertSafeIdentifier(context.id, "context id");
    if (contextIds.has(contextId)) fail(`duplicate context ${contextId}`);
    assertString(context.source_id, `context ${contextId} source_id`);
    assertString(context.unit_id, `context ${contextId} unit_id`);
    assertString(context.label, `context ${contextId} label`);
    if (!Object.hasOwn(context, "document")) fail(`context ${contextId} document is required`);
    contextIds.add(contextId);
  }
  return { snapshotId, identity, questions, objectIds, facetKeys, contextIds, text: source.text };
}

function makeBlankState(index) {
  return {
    schema: DRAFT_SCHEMA,
    snapshot_id: index.snapshotId,
    source: { ...index.identity },
    selected_options: Object.create(null),
    decisions: [],
  };
}

function assertIdentity(index, state) {
  if (!isPlainObject(state)) fail("draft state must be an object");
  assertOnlyKeys(state, STATE_KEYS, "draft state");
  if (state.schema !== DRAFT_SCHEMA) fail("draft schema is not ScholarSandboxDrafts/1");
  if (state.snapshot_id !== index.snapshotId) fail("draft snapshot_id does not match snapshot");
  if (!isPlainObject(state.source)) fail("draft source must be an object");
  assertOnlyKeys(state.source, DRAFT_SOURCE_KEYS, "draft source");
  for (const [key, value] of Object.entries(index.identity)) {
    if (state.source[key] !== value) fail(`draft source.${key} does not match snapshot`);
  }
}

function assertQuestionOption(index, questionId, optionId, label = "draft") {
  assertSafeIdentifier(questionId, `${label}.question_id`);
  assertSafeIdentifier(optionId, `${label}.option_id`);
  const options = index.questions.get(questionId);
  if (!options) fail(`${label}.question_id is unknown`);
  const option = options.get(optionId);
  if (!option) fail(`${label}.option_id is unknown for question ${questionId}`);
  return option;
}

function validateAnchor(index, anchor) {
  if (!isPlainObject(anchor)) fail("draft.anchor must be an object");
  assertOnlyKeys(anchor, ANCHOR_KEYS, "draft.anchor");
  const { doc_id, reading_id, source_sha256, start, end, quote, offset_unit } = anchor;
  if (doc_id !== index.identity.doc_id) fail("draft.anchor.doc_id does not match snapshot source");
  if (reading_id !== index.identity.reading_id) fail("draft.anchor.reading_id does not match snapshot source");
  if (source_sha256 !== index.identity.text_sha256) fail("draft.anchor.source_sha256 does not match snapshot source");
  if (offset_unit !== "unicode_code_point") fail("draft.anchor.offset_unit must be unicode_code_point");
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end <= start) {
    fail("draft.anchor must have a non-empty integer source range");
  }
  const characters = Array.from(index.text);
  if (end > characters.length) fail("draft.anchor range is outside snapshot source text");
  const exactQuote = characters.slice(start, end).join("");
  if (quote !== exactQuote) fail("draft.anchor.quote does not exactly match snapshot source text");
  return { doc_id, reading_id, source_sha256, start, end, quote, offset_unit };
}

function validateRecord(index, value, { generateId = false } = {}) {
  if (!isPlainObject(value)) fail("draft record must be an object");
  assertOnlyKeys(value, RECORD_KEYS, "draft record");
  const record = safeCopy(value);
  if (!record.id && generateId) record.id = newDraftId();
  assertSafeIdentifier(record.id, "draft record id");
  if (!["option", "term_boundary", "context"].includes(record.kind)) fail("draft record kind is invalid");
  if (record.status !== "draft") fail("draft record status must be draft");
  record.anchor = validateAnchor(index, record.anchor);
  if (!isPlainObject(record.inputs)) fail("draft record inputs must be a JSON object");
  assertSafeJson(record.inputs, "draft record inputs");
  record.inputs = safeCopy(record.inputs);
  if (typeof record.reason !== "string") fail("draft record reason must be a string");

  const hasQuestion = Object.hasOwn(record, "question_id") || Object.hasOwn(record, "option_id");
  if (hasQuestion) record.option = assertQuestionOption(index, record.question_id, record.option_id, "draft record");
  if (Object.hasOwn(record, "object_id")) {
    assertSafeIdentifier(record.object_id, "draft record object_id");
    if (!index.objectIds.has(record.object_id)) fail("draft record object_id is unknown");
  }
  if (Object.hasOwn(record, "facet_key")) {
    assertSafeIdentifier(record.facet_key, "draft record facet_key");
    if (!index.facetKeys.has(record.facet_key)) fail("draft record facet_key is unknown");
  }

  if (record.kind === "option") {
    if (!hasQuestion) fail("option draft requires question_id and option_id");
    if (Object.hasOwn(record, "context_id")) fail("option draft cannot contain context_id");
  } else if (record.kind === "term_boundary") {
    if (hasQuestion || Object.hasOwn(record, "context_id")) fail("term_boundary draft cannot contain question or context fields");
  } else {
    if (!hasQuestion) fail("context draft requires question_id and option_id");
    if (record.option.action !== "attach_context") fail("context draft requires an attach_context option");
    assertSafeIdentifier(record.context_id, "draft record context_id");
    if (!index.contextIds.has(record.context_id)) fail("draft record context_id is unknown");
  }
  delete record.option;
  return record;
}

function newDraftId() {
  const randomUUID = globalThis.crypto?.randomUUID;
  if (typeof randomUUID !== "function") fail("crypto.randomUUID is unavailable for draft id generation");
  return randomUUID.call(globalThis.crypto);
}

function assertStorage(storage) {
  if (!storage || typeof storage.getItem !== "function" || typeof storage.setItem !== "function") {
    fail("storage must provide getItem and setItem");
  }
}

export function createDraftState(snapshot) {
  return makeBlankState(snapshotIndex(snapshot));
}

export function validateDraftState(snapshot, value) {
  const index = snapshotIndex(snapshot);
  assertIdentity(index, value);
  if (!isPlainObject(value.selected_options)) fail("draft selected_options must be an object");
  if (!Array.isArray(value.decisions)) fail("draft decisions must be an array");
  const state = makeBlankState(index);
  for (const [questionId, optionId] of Object.entries(value.selected_options)) {
    assertSafeKey(questionId, "draft selected_options");
    assertQuestionOption(index, questionId, optionId, "draft selected_options");
    state.selected_options[questionId] = optionId;
  }
  const ids = new Set();
  for (const decision of value.decisions) {
    const normalized = validateRecord(index, decision);
    if (ids.has(normalized.id)) fail(`duplicate draft record id ${normalized.id}`);
    ids.add(normalized.id);
    state.decisions.push(normalized);
  }
  return state;
}

export function selectOption(snapshot, state, questionId, optionId) {
  const index = snapshotIndex(snapshot);
  const next = validateDraftState(snapshot, state);
  assertQuestionOption(index, questionId, optionId, "selected option");
  next.selected_options[questionId] = optionId;
  return next;
}

export function upsertDraft(snapshot, state, record) {
  const index = snapshotIndex(snapshot);
  const next = validateDraftState(snapshot, state);
  const normalized = validateRecord(index, record, { generateId: !record?.id });
  const found = next.decisions.findIndex(decision => decision.id === normalized.id);
  if (found === -1) next.decisions.push(normalized);
  else next.decisions[found] = normalized;
  return next;
}

export function retractDraft(snapshot, state, id) {
  assertSafeIdentifier(id, "draft record id");
  const next = validateDraftState(snapshot, state);
  next.decisions = next.decisions.filter(decision => decision.id !== id);
  return next;
}

export function exportDrafts(snapshot, state) {
  return JSON.stringify(validateDraftState(snapshot, state));
}

export function importDrafts(snapshot, text) {
  if (typeof text !== "string") fail("draft import must be a JSON string");
  if (new TextEncoder().encode(text).byteLength > MAX_IMPORT_BYTES) fail("draft import exceeds 5 MB limit");
  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    fail("draft import is not valid JSON");
  }
  return validateDraftState(snapshot, parsed);
}

export function draftStorageKey(snapshot) {
  return `scholar-sandbox-drafts:${encodeURIComponent(snapshotIndex(snapshot).snapshotId)}`;
}

export function loadDrafts(snapshot, storage = globalThis.localStorage) {
  assertStorage(storage);
  const stored = storage.getItem(draftStorageKey(snapshot));
  if (stored === null) return createDraftState(snapshot);
  if (typeof stored !== "string") fail("stored drafts must be a JSON string");
  return importDrafts(snapshot, stored);
}

export function saveDrafts(snapshot, state, storage = globalThis.localStorage) {
  assertStorage(storage);
  const safeState = validateDraftState(snapshot, state);
  storage.setItem(draftStorageKey(snapshot), JSON.stringify(safeState));
  return safeState;
}

export function makeSourceAnchor(snapshot, start, end) {
  const index = snapshotIndex(snapshot);
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end <= start) {
    fail("source anchor must have a non-empty integer range");
  }
  const characters = Array.from(index.text);
  if (end > characters.length) fail("source anchor range is outside snapshot source text");
  return {
    doc_id: index.identity.doc_id,
    reading_id: index.identity.reading_id,
    source_sha256: index.identity.text_sha256,
    start,
    end,
    quote: characters.slice(start, end).join(""),
    offset_unit: "unicode_code_point",
  };
}
