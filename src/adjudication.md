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
    <p class="entry-card-note"><a href="{{ '/methodology/' | url }}">Methodology / Ontology Reference：术语、证据边界与禁止推断</a></p>
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
    <section class="filter-box" aria-labelledby="processing-title">
      <h2 id="processing-title" class="section-title is-small">System processing flow</h2>
      <p class="entry-card-note">这是分析系统的实际产物记录；它不同于原文内部的算法步骤。</p>
      <div id="system-stages" class="research-stage-list"></div>
    </section>
    <section class="filter-box workbench-session-tools" aria-labelledby="session-title">
      <h2 id="session-title" class="section-title is-small">Reviewed analysis session</h2>
      <p id="session-status" class="entry-card-note" role="status" aria-live="polite"></p>
      <label for="branch-select">Active branch</label><select id="branch-select"></select>
      <label for="branch-name">New interpretation branch</label><input id="branch-name" type="text" autocomplete="off">
      <button id="create-branch" type="button">Create branch</button>
      <button id="export-session" type="button">Export session</button>
      <label class="object-select">Import session <input id="import-session" type="file" accept="application/json"></label>
    </section>
    <div class="workbench-columns">
      <section class="research-panel" aria-labelledby="source-title">
        <h2 id="source-title" class="section-title is-small">Source / Context</h2>
        <label for="annotation-layer">Annotation layer</label>
        <select id="annotation-layer"><option value="all">All layers</option><option value="L0">L0 source / reading</option><option value="L1">L1 procedure / stage</option><option value="L2">L2 construction / control</option><option value="L3">L3 term / quantity</option></select>
        <p class="entry-card-note">高亮按原文字符范围定位；相同词形不自动合并。点击范围可作为当前审核目标。</p>
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
      <h2 id="issues-title" class="section-title is-small">Current review question / evidence</h2>
      <p class="entry-card-note">问题来自 reviewed compiler；候选、证据、下游影响和允许动作会随重新编译更新。</p>
      <div id="review-queue"></div>
      <div id="analysis-issues"></div>
    </section>
    <section class="filter-box" aria-labelledby="decision-title">
      <h2 id="decision-title" class="section-title is-small">Adjudication actions</h2>
      <p id="selected-anchor" class="entry-card-note" role="status">先从原文、结构或问题选择一个 source span。</p>
      <div class="workbench-action-grid">
        <label>Candidate <select id="candidate-select"></select></label>
        <button id="select-candidate" data-action="select_candidate" type="button"></button>
        <button id="reject-candidate" data-action="reject_candidate" type="button"></button>
        <label>Split at source character offset <input id="split-at" type="number" min="0"></label>
        <button id="resegment" data-action="resegment" type="button"></button>
        <label>Known type <select id="manual-operation"></select></label>
        <button id="assemble-known" data-action="assemble_known_structure" type="button"></button>
        <label>Lexical role <select id="lexical-role"></select></label>
        <button id="apply-lexical-role" data-action="set_lexical_role" type="button"></button>
        <button id="mark-unresolved" data-action="defer:unresolved" type="button"></button>
        <button id="request-extension" data-action="defer:schema_extension_required" type="button"></button>
      </div>
      <details class="research-disclosure"><summary>Binding, scope, profile, and context</summary>
        <div class="workbench-action-grid">
          <label>Consumer definition <select id="binding-consumer"></select></label>
          <label>Producer definition <select id="binding-producer"></select></label>
          <label>Formal / input slot <input id="binding-formal" type="text"></label>
          <label>Producer output port <select id="binding-port"></select></label>
          <button id="apply-binding" data-action="bind_value" type="button"></button>
          <label>Procedure or stage <select id="scope-definition"></select></label>
          <label>Query base <select id="scope-base"></select></label>
          <button id="apply-scope" data-action="set_scope" type="button"></button>
          <label>Profile <select id="profile-select"></select></label>
          <button id="apply-profile" data-action="select_profile" type="button"></button>
          <label>Existing context <select id="context-select"></select></label>
          <button id="attach-context" data-action="attach_context" type="button"></button>
          <label>Root parameter <input id="parameter-name" type="text"></label>
          <label>Unit <select id="parameter-unit"></select></label>
          <button id="declare-parameter" data-action="declare_parameter" type="button"></button>
        </div>
      </details>
      <h3 class="entry-card-title">Decision history</h3><div id="decision-history"></div>
    </section>
    <details id="numerical-check" class="filter-box research-disclosure">
      <summary>Numerical reconstruction / consistency check</summary>
      <p class="entry-card-note">对当前结构进行辅助数值验证。输入值不改变原文或分析结构。</p>
      <form id="execute-form" class="search-controls">
        <div id="inputs"></div>
        <button id="execute" type="submit">Execute</button>
      </form>
      <p id="execution-status" role="status" aria-live="polite">尚未执行。Graph computed、source-attested 与 scholar-reconstructed 的比较均独立显示。</p>
      <div id="execution-result" hidden><pre id="outputs"></pre><details data-debug="true"><summary>调试／原始执行记录</summary><pre id="execution-raw"></pre></details></div>
    </details>
    <details id="graph-json" class="research-disclosure" data-debug="true">
      <summary>原始 IR / graph JSON</summary><pre id="graph-raw"></pre>
    </details>
  </div>
</div>
<script type="module" src="{{ '/js/procedure-workbench.js' | url }}"></script>
