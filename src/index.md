---
layout: base
title: Home
---

{% if page.url == "/" %}
  <!-- Banner Hero -->
  <div class="hero">
    <h1>MATHesis</h1>
    <p>A Tool for Mapping Ancient Mathematical Expressions</p>
  </div>
{% endif %}

<section id="intro" class="intro-text">
  <p>
    <strong>MATHesis</strong> is an exploratory digital tool for mapping how numbers and mathematical operations were symbolically expressed and organized in Chinese and Sanskrit contexts. Using a node-based model anchored to specific textual passages, it allows users to explore numerical and symbolic expressions across texts and traditions.
  </p>
</section>

<p style="text-align: center; margin-top: 2rem;">
  <a href="{{ '/search/' | url }}" class="cta-button">Start Exploring</a>
</p>


<!-- 原来的 search filter 等照常写 -->
