import {
  extractHeadingCandidate,
  normalizeWhitespace,
  readJson,
  readPipelineConfig,
  writeJson,
  inferCullenSystem,
} from "./cullen-oracle-common.mjs";

const MAX_CHUNK_CHARS = 1600;

function paragraphUnits(page) {
  return page.normalized_text
    .split(/\n{2,}/u)
    .map((paragraph) => normalizeWhitespace(paragraph))
    .filter((paragraph) => paragraph.length >= 40)
    .map((paragraph, index) => ({
      page_number: page.page_number,
      paragraph_index: index,
      text: paragraph,
      heading_candidate: extractHeadingCandidate(paragraph),
      system_hint: inferCullenSystem(paragraph),
    }));
}

function buildChunks(pages) {
  const units = pages.flatMap(paragraphUnits);
  const chunks = [];
  let buffer = [];
  let size = 0;

  function flush() {
    if (!buffer.length) return;
    const text = buffer.map((item) => item.text).join("\n\n");
    const pageStart = buffer[0].page_number;
    const pageEnd = buffer[buffer.length - 1].page_number;
    const heading = buffer.find((item) => item.heading_candidate)?.heading_candidate ?? null;
    const system = buffer.find((item) => item.system_hint)?.system_hint ?? inferCullenSystem(text);
    chunks.push({
      id: `cullen:chunk:${chunks.length + 1}`,
      page_start: pageStart,
      page_end: pageEnd,
      heading,
      system_hint: system,
      text,
      char_count: text.length,
      paragraph_refs: buffer.map((item) => ({
        page_number: item.page_number,
        paragraph_index: item.paragraph_index,
      })),
    });
    buffer = [];
    size = 0;
  }

  for (const unit of units) {
    const startsNewSection = Boolean(unit.heading_candidate);
    if (buffer.length && (startsNewSection || size + unit.text.length > MAX_CHUNK_CHARS)) flush();
    buffer.push(unit);
    size += unit.text.length;
  }
  flush();
  return chunks;
}

async function main() {
  const config = await readPipelineConfig();
  const pagesPayload = await readJson(config.inputs.cullen.artifacts.pages);
  const chunks = buildChunks(pagesPayload.pages);
  await writeJson(config.inputs.cullen.artifacts.chunks, {
    generated_at: new Date().toISOString(),
    source_pdf: pagesPayload.source_pdf,
    page_count: pagesPayload.page_count,
    chunk_count: chunks.length,
    chunks,
  });
  console.log(JSON.stringify({
    stage: "build-cullen-chunks",
    chunks: chunks.length,
    output: config.inputs.cullen.artifacts.chunks,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
