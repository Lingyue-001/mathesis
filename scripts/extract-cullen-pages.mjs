import { spawn } from "node:child_process";
import path from "node:path";
import { readPipelineConfig, resolveRepoPath } from "./cullen-oracle-common.mjs";

async function runPython(args) {
  await new Promise((resolve, reject) => {
    const child = spawn("python", args, {
      cwd: process.cwd(),
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stderr = "";
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(stderr || `Python exited with code ${code}`));
    });
  });
}

async function main() {
  const config = await readPipelineConfig();
  const inputPdf = resolveRepoPath(config.inputs.cullen.path);
  const outputJson = resolveRepoPath(config.inputs.cullen.artifacts.pages);
  const helperScript = resolveRepoPath(path.join("scripts", "extract_cullen_pages.py"));

  await runPython([helperScript, inputPdf, outputJson]);
  console.log(JSON.stringify({
    stage: "extract-cullen-pages",
    output: config.inputs.cullen.artifacts.pages,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
