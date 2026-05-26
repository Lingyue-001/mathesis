---
title: MATHesis – Search
layout: base
---

<!-- 下面贴上你现有那段搜索 HTML -->

<div class="search-page">

<div class="filter-box" style="max-width: 1000px; margin-bottom: 2rem;">
  <section class="search-hero">
  <h1 class="page-kicker">Keyword Search</h1>
</section>
  <div class="search-controls" style="display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;">
    <input
      type="text"
      id="searchInput"
      placeholder="Enter keyword, e.g. '144', 'moon', '成法'..."
      style="flex: 1 1 400px; min-width: 200px; max-width: 300px; padding: 0.25rem; border: 1px solid #ccc; border-radius: 4px;"
    />
    <button
      id="searchBtn"
      type="button"
      style="width: 100px; padding: 0.25rem 1rem;"
    >Search</button>
    <select id="categorySelect" style="width: 150px; padding: 0.25rem; text-align: center; text-align-last: center;">
      <option value="All">All Categories</option>
      <option value="symbol">Chinese Symbol</option>
      <option value="number">Number</option>
      <option value="sanskritsymbol">Sanskrit Symbol</option>
    </select>
    <span class="hover-tooltip" data-tooltip="Filter results by symbolic, structural, or operational relationship type.">
      <select id="relationSelect" style="width: 150px; padding: 0.25rem; text-align: center; text-align-last: center;">
        <option value="All">All Relations</option>
        <option value="IS_UNIT_IN">is unit in</option>
        <option value="PART_OF_STRUCTURE">part of structure</option>
        <option value="PRODUCES">produces</option>
        <option value="REPRESENTS">represents</option>
        <option value="RESULTS_IN">results in</option>
        <option value="SUPPORTS">supports</option>
        <option value="SYMBOLIZES">symbolizes</option>
      </select>
    </span>
  </div>

  <h3 class="section-title is-small">Filter Fields</h3>
  <label class="hover-tooltip" data-tooltip="Supports searching Chinese (Simplified/Traditional), English, Sanskrit, and numbers.">
  <input type="checkbox" class="field-type" value="entry" /> Entry Name
</label><br />

<label class="hover-tooltip" data-tooltip="Includes definitions, symbolic meanings, explanations, and related concepts.">
  <input type="checkbox" class="field-type" value="meaning" /> Meaning
</label><br />

<label class="hover-tooltip" data-tooltip="Includes symbolic systems like Yin-Yang, image-number systems, calendar logic, etc.">
  <input type="checkbox" class="field-type" value="system" /> System
</label><br />

<label class="hover-tooltip" data-tooltip="Includes references from primary and secondary sources.">
  <input type="checkbox" class="field-type" value="source" /> Source
</label><br />

<label class="hover-tooltip" data-tooltip="Matches terms connected to this one via symbolic relationships.">
  <input type="checkbox" class="field-type" value="related" /> Related Nodes
</label>
  
</div>


<hr style="
  border: none;
  border-top: 1px solid rgba(157, 103, 49, 0.43); /* 浅棕木系 */
  margin: 2rem auto;
  width: 80%;
">



<!-- 新增：搜索结果数量显示 -->
<div id="resultCount" style="
  margin: 1.5rem 0;
  font-weight: bold;
  text-align: center;
  color:rgba(157, 103, 49, 0.81); /* 一种温润木色，你可以换成自己喜欢的 */
  font-size: 1.1rem;
"></div>


<!-- 原有：搜索结果卡片容器 -->
<div id="results" class="results-box"></div>

<script type="module" src="{{ '/js/filter.js' | url }}"></script>


</div>
