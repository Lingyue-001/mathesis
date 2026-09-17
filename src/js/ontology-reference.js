// Pure rendering of the canonical backend registry; no glossary or code map.
import { element } from './ui/procedure-view.js';
const base = document.documentElement.dataset.baseurl || '/';
try {
  const response = await fetch(`${base.replace(/\/?$/, '/') }api/ontology`);
  if (!response.ok) throw new Error('registry_unavailable');
  const registry = await response.json();
  document.getElementById('ontology-status').textContent = `目录版本 ${registry.version} · ${registry.entries.length} 个条目`;
  const container = document.getElementById('ontology-reference');
  for (const row of registry.entries) {
    const card = element('article', 'entry-card');
    card.dataset.ontologyCategory = row.category; card.dataset.ontologyCode = row.code;
    card.append(element('h2', 'entry-card-title', row.label), element('p', '', row.definition), element('p', '', row.methodology));
    card.append(element('p', 'entry-card-note', `不能据此推断：${row.must_not_infer.join('；')}`));
    const debug = element('details'); debug.dataset.debug = 'true';
    debug.append(element('summary', '', '机器协议与字段（调试／溯源）'), element('pre', '', JSON.stringify({ code: row.code, category: row.category, hierarchy: row.hierarchy, required_fields: row.required_fields }, null, 2)));
    card.append(debug); container.append(card);
  }
} catch (error) {
  document.getElementById('ontology-status').textContent = '尚未连接本地目录服务。请通过本地 Workbench 打开。';
  console.debug(error);
}
