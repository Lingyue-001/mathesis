import {
  readJson,
  readPipelineConfig,
  tokenizeEnglish,
  unique,
  writeJson,
} from "./cullen-oracle-common.mjs";

function buildIndex(chunks) {
  const postings = new Map();
  for (const chunk of chunks) {
    for (const token of unique(tokenizeEnglish(chunk.text))) {
      if (!postings.has(token)) postings.set(token, []);
      postings.get(token).push(chunk.id);
    }
  }
  return Object.fromEntries([...postings.entries()].sort(([left], [right]) => left.localeCompare(right)));
}

async function main() {
  const config = await readPipelineConfig();
  const chunkPayload = await readJson(config.inputs.cullen.artifacts.chunks);
  const index = buildIndex(chunkPayload.chunks);
  await writeJson(config.inputs.cullen.artifacts.search_index, {
    generated_at: new Date().toISOString(),
    chunk_count: chunkPayload.chunk_count,
    vocabulary_size: Object.keys(index).length,
    postings: index,
  });
  console.log(JSON.stringify({
    stage: "build-cullen-search-index",
    vocabulary_size: Object.keys(index).length,
    output: config.inputs.cullen.artifacts.search_index,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
