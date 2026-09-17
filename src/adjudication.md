---
title: Procedure Workbench
layout: base
templateEngineOverride: liquid
---
<link rel="stylesheet" href="{{ '/css/research.css' | url }}">
<link rel="stylesheet" href="{{ '/css/workbench.css' | url }}">
<div class="search-page procedure-workbench">
  <section class="search-hero">
    <h1 class="page-kicker">Procedure Workbench</h1>
    <p>Source ↔ Procedure structure ↔ Graph</p>
    <p class="entry-card-note">并置阅读原文与计算过程。点击原文、步骤或图节点，追踪它们之间的来源与数量关系。</p>
  </section>
  <section class="filter-box search-controls workbench-controls" aria-label="Procedure selection">
    <label for="procedure">Procedure</label>
    <select id="procedure" disabled></select>
    <button id="analyze" type="button" disabled>重新分析结构</button>
    <p id="scope" class="entry-card-note"></p>
  </section>
  <p id="status" role="status" aria-live="polite">正在读取 procedure…</p>
  <div id="analysis" hidden>
    <div class="workbench-columns">
      <section class="research-panel" aria-labelledby="source-title">
        <h2 id="source-title" class="section-title is-small">Source / Context</h2>
        <p class="entry-card-note">高亮按原文字符范围定位；相同词形不自动合并。</p>
        <div id="source" class="research-scroll"></div>
      </section>
      <section class="research-panel" aria-labelledby="structure-title">
        <h2 id="structure-title" class="section-title is-small">Procedure structure</h2>
        <p class="entry-card-note">Procedure → query / stage → 按原文顺序排列的操作。</p>
        <div id="structure" class="research-scroll"></div>
      </section>
      <section class="research-panel" aria-labelledby="graph-title">
        <h2 id="graph-title" class="section-title is-small">Typed graph</h2>
        <p id="graph-summary" class="entry-card-note"></p>
        <div id="graph" class="research-scroll"></div>
      </section>
    </div>
    <section class="filter-box" aria-labelledby="selection-title">
      <h2 id="selection-title" class="section-title is-small">Selection / typed relationships</h2>
      <p id="selection-status" role="status" aria-live="polite">选择一个步骤，查看 quantity roles、端口、依赖、unit / scale 与 scope / control。</p>
      <div id="selection-detail"></div>
    </section>
    <section class="filter-box" aria-labelledby="issues-title">
      <h2 id="issues-title" class="section-title is-small">Unresolved / structure diagnostics</h2>
      <p class="entry-card-note">保留 IR 的未知类型与各层诊断；数值执行成功不会消除这些问题。</p>
      <div id="analysis-issues"></div>
    </section>
    <details id="numerical-check" class="filter-box research-disclosure">
      <summary>Numerical reconstruction / consistency check</summary>
      <p class="entry-card-note">对当前结构进行辅助数值验证。输入值不改变原文或分析结构。</p>
      <form id="execute-form" class="search-controls">
        <div id="inputs"></div>
        <button id="execute" type="submit">Execute</button>
      </form>
      <p id="execution-status" role="status" aria-live="polite">尚未执行。</p>
      <div id="execution-result" hidden><pre id="outputs"></pre><details><summary>Execution / unresolved</summary><pre id="execution-raw"></pre></details></div>
    </details>
    <details id="graph-json" class="research-disclosure">
      <summary>原始 IR / graph JSON</summary><pre id="graph-raw"></pre>
    </details>
  </div>
</div>
<script type="module" src="{{ '/js/procedure-workbench.js' | url }}"></script>
