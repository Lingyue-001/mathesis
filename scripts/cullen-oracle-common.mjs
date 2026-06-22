import fs from "node:fs/promises";
import path from "node:path";

export const ROOT = process.cwd();
export const CONFIG_PATH = path.join(ROOT, "config", "calendrical-ir-pipeline.json");

export async function readPipelineConfig() {
  return JSON.parse(await fs.readFile(CONFIG_PATH, "utf8"));
}

export function resolveRepoPath(relativePath) {
  return path.join(ROOT, relativePath);
}

export function normalizeWhitespace(text) {
  return text
    .replace(/\u00ad/gu, "")
    .replace(/\s+/gu, " ")
    .trim();
}

export function splitIntoSentences(text) {
  return text
    .split(/(?<=[.!?])\s+/u)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
}

export function tokenizeEnglish(text) {
  return normalizeWhitespace(text)
    .toLowerCase()
    .split(/[^a-z0-9]+/u)
    .filter((token) => token.length >= 3);
}

export function unique(items) {
  return [...new Set(items)];
}

export async function writeJson(relativePath, data) {
  const target = resolveRepoPath(relativePath);
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.writeFile(target, `${JSON.stringify(data, null, 2)}\n`, "utf8");
}

export async function readJson(relativePath) {
  return JSON.parse(await fs.readFile(resolveRepoPath(relativePath), "utf8"));
}

export function extractAsciiNumberValues(text) {
  return [...text.matchAll(/\b\d+(?:\.\d+)?\b/gu)].map((match) => Number(match[0]));
}

export function inferCullenSystem(text) {
  const lowered = text.toLowerCase();
  if (/(three concordance|triple concordance|santong)/u.test(lowered)) return "santong";
  if (/(quarter remainder|four parts|four-part|sifen)/u.test(lowered)) return "sifen";
  if (/(qianxiang|dry semblance|eastern han)/u.test(lowered)) return "qianxiang_or_houhan";
  return null;
}

export function extractHeadingCandidate(text) {
  const lines = text.split(/\n+/u).map((line) => line.trim()).filter(Boolean);
  for (const line of lines.slice(0, 4)) {
    if (/^(?:\d+(?:\.\d+)*)?\s*[A-Z][A-Za-z0-9 ,.'()[\]-]{4,}$/u.test(line)) {
      return line;
    }
  }
  return null;
}
