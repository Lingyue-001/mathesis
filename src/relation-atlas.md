---
title: MATHesis - Visual Grammar
layout: base
templateEngineOverride: liquid
---

<div class="relation-demo-app">
  <section class="relation-demo-header">
    <div>
      <h1>Visual Grammar</h1>
      <p class="relation-demo-subtitle">
        A source-backed visual grammar for Cullen chapter 3 annotations: concepts, relation frames,
        procedure steps, role shifts, and chunk-level evidence.
      </p>
    </div>
    <div class="relation-demo-stats" id="relationStats"></div>
  </section>

  <nav class="relation-demo-tabs" id="relationTabs" aria-label="Visual grammar views">
    <button class="relation-demo-tab active" type="button" data-view="concept">Concept to Computation</button>
    <button class="relation-demo-tab" type="button" data-view="grammar">Relation Visual Grammar</button>
    <button class="relation-demo-tab" type="button" data-view="operations">Operation Clusters</button>
    <button class="relation-demo-tab" type="button" data-view="matrix">Role-Shift Matrix</button>
    <button class="relation-demo-tab" type="button" data-view="explorer">Chunk Explorer</button>
  </nav>

  <main class="relation-demo-grid">
    <section>
      <div id="view-concept" class="relation-demo-view active relation-demo-panel pad"></div>
      <div id="view-grammar" class="relation-demo-view relation-demo-panel pad"></div>
      <div id="view-operations" class="relation-demo-view relation-demo-panel pad"></div>
      <div id="view-matrix" class="relation-demo-view relation-demo-panel pad"></div>
      <div id="view-explorer" class="relation-demo-view relation-demo-panel pad"></div>
    </section>
    <aside class="relation-demo-panel relation-demo-inspector" id="relationInspector"></aside>
  </main>
</div>

<!--
  The route remains /relation-atlas/ for compatibility, but the user-facing page name is Visual Grammar.
-->

<script type="module" src="{{ '/js/relation-atlas.js' | url }}"></script>
