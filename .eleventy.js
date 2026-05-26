require("./scripts/load-local-env.cjs");

const { createCtextSearchMiddleware } = require("./server/ctextSearchMiddleware");

module.exports = function(eleventyConfig) {
  // === 静态资源复制 ===
  eleventyConfig.addPassthroughCopy("src/js");
  eleventyConfig.addPassthroughCopy("src/css");
  eleventyConfig.addPassthroughCopy("assets/fonts");
  eleventyConfig.addPassthroughCopy("static");
  eleventyConfig.addPassthroughCopy("src/transcriptions/tei_hanshu");
  eleventyConfig.addPassthroughCopy("src/transcriptions/tei_brhat");
  eleventyConfig.addPassthroughCopy("src/data.json");
  eleventyConfig.addPassthroughCopy("simp_to_trad_map.json");
  eleventyConfig.addPassthroughCopy("assets");

  // === 环境变量判断 ===
  // Only GitHub Actions project-site builds should use /mathesis pathPrefix.
  const isProduction = process.env.NODE_ENV === "production";
  const isNetlifyBuild = String(process.env.NETLIFY || "").toLowerCase() === "true";
  const isGitHubActionsBuild = String(process.env.GITHUB_ACTIONS || "").toLowerCase() === "true";
  const pathPrefix = isGitHubActionsBuild ? "/mathesis/" : "/";

  const ctextMiddleware = createCtextSearchMiddleware();
  const ctextProxyOrigin = String(process.env.CTEXT_PROXY_ORIGIN || "").trim();
  eleventyConfig.addGlobalData("ctextProxyOrigin", ctextProxyOrigin);

  // Eleventy v3 dev server path
  if (typeof eleventyConfig.setServerOptions === "function") {
    eleventyConfig.setServerOptions({
      middleware: [ctextMiddleware]
    });
  }

  // Eleventy v2 BrowserSync path (fallback/compat)
  if (typeof eleventyConfig.setBrowserSyncConfig === "function") {
    eleventyConfig.setBrowserSyncConfig({
      middleware: [ctextMiddleware]
    });
  }

  const outputDir = (isProduction || isNetlifyBuild) ? "dist" : "_site";

  // === 目录结构设置 ===
  return {
    pathPrefix,
    dir: {
      input: "src",          // 源文件夹
      includes: "layouts",   // 模板所在位置
      data: "data",          // 数据目录（可选）
      output: outputDir // 🧩 Netlify/GitHub Actions builds should publish from dist
    }
  };
};
