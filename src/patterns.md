---
title: MATHesis - Pattern Lab
layout: base
templateEngineOverride: liquid
---

<div class="search-page pattern-lab-page">
  <nav class="pattern-side-index" aria-label="Pattern page sections">
    <span>Sections</span>
    <a href="#pattern-lab">Pattern Index</a>
    <a href="#reference-alignment-lab">Reference Alignment Lab</a>
  </nav>

  <section id="pattern-lab" class="search-hero pattern-hero">
    <h1 class="page-kicker">Pattern Lab</h1>
  </section>

  <section class="filter-box pattern-browser">
    <div class="pattern-section-head">
      <div>
        <h2 class="section-title is-small">Pattern Index</h2>
        <p class="pattern-lab-note">
          Browse algorithmic patterns by chunk, evidence family, annotation source, and alignment strength.
          This section is for comparing computational structure and term roles.
          Switch between single chunk records and paired alignments.
        </p>
      </div>
      <div class="pattern-mode-switch is-pairs" aria-label="Pattern index mode">
        <button type="button" data-pattern-mode="chunks">Single Chunk Index</button>
        <button class="is-active" type="button" data-pattern-mode="pairs">Pairwise Alignment</button>
      </div>
    </div>

    <div class="search-controls pattern-lab-controls">
      <label class="pattern-control-label" for="patternSearch">Search</label>
      <input
        id="patternSearch"
        type="text"
        placeholder="Search Proc, chunk id, Chinese text, motif, term, e.g. Proc. 3.25 or 宿次"
      />
      <button id="patternSearchBtn" type="button">Search</button>
      <select id="patternAnnotation">
        <option value="all">All annotation sources</option>
        <option value="manual_steps">Manual step references</option>
        <option value="manual_breakdown">Manual breakdown chunks</option>
        <option value="machine">Machine extracted chunks</option>
      </select>
      <select id="patternEvidence">
        <option value="all">All evidence families</option>
        <option value="operation_skeleton">Operation skeleton</option>
        <option value="quantity_flow">Quantity flow</option>
        <option value="parameter_role">Parameter role</option>
        <option value="target_output_class">Target/output class</option>
        <option value="surface_wording">Surface wording</option>
        <option value="term_overlap">Term overlap</option>
      </select>
    </div>
    <details class="pattern-similarity-criteria">
      <summary>Similarity criteria</summary>
      <div class="pattern-scoring-grid">
        <p><strong>Operation skeleton</strong> = ordered comparison of <code>steps.op</code>.</p>
        <p><strong>Quantity flow</strong> = comparison of input/output roles and remainder/date channels.</p>
        <p><strong>Parameter role</strong> = comparison of multiplier, divisor, modulus, threshold, and counting-frame roles.</p>
        <p><strong>Target/output class</strong> = comparison of final output type.</p>
        <p><strong>Surface wording</strong> = phrase overlap, low weight.</p>
        <p><strong>Term overlap</strong> = shared technical terms, low-to-medium weight.</p>
      </div>
      <p class="pattern-lab-note">
        The comparison is reproducible because each axis is computed from the derived chunk index, not by ad hoc reading:
        ordered operation labels, role bindings, named outputs, phrase patterns, and shared technical terms are counted
        the same way for every pair. Strong similarity requires broad agreement across structure and semantic-role axes,
        including either Quantity flow or Target/output class; operation order alone, surface wording alone, or term
        overlap alone cannot produce a strong match.
      </p>
    </details>

    <section id="patternSummary" class="pattern-lab-summary" aria-live="polite"></section>
  </section>

  <section class="pattern-lab-section">
    <div class="pattern-section-head">
      <h2 id="patternResultsTitle" class="section-title">Alignment Review</h2>
      <span id="patternResultsMeta" class="pattern-results-meta"></span>
      <div id="patternSortControls" class="pattern-sort-toggles" aria-label="Sort order"></div>
    </div>
    <div id="comparisonResults" class="pattern-lab-results" aria-live="polite"></div>
  </section>

  <section id="reference-alignment-lab" class="filter-box pattern-reference-lab">
    <h2 class="section-title is-small">Reference Alignment Lab</h2>
    <p class="pattern-lab-note">
      Use a manually annotated reference chunk on the left and compare it with any extracted chunk on the right.
      This is computed live in the browser from the same feature index.
    </p>
    <div class="search-controls pattern-lab-controls">
      <select id="compareA"></select>
      <select id="compareB"></select>
      <button id="compareBtn" type="button">Compare</button>
    </div>
    <div id="manualCompareResult" class="pattern-lab-results pattern-manual-compare"></div>
  </section>
</div>

<script type="module" src="{{ '/js/patterns.js' | url }}"></script>
