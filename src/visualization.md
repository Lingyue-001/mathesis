---
title: MATHesis – Visualization
layout: base
---

<div class="graph-shell">
  <div id="graph-container" class="graph-canvas"></div>
  <div class="graph-controls" aria-label="Graph controls">
    <button class="graph-btn" id="zoomIn" type="button">+</button>
    <button class="graph-btn" id="zoomOut" type="button">−</button>
  </div>
</div>

<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<script>
async function drawGraph() {
  const baseUrl = document.documentElement.dataset.baseurl || "/";
  const withBase = (path) => `${baseUrl.replace(/\/?$/, "/")}${path.replace(/^\/+/, "")}`;

  // 加载 CSV 数据
  const nodeCsv = await fetch(withBase("static/node-export.csv")).then(res => res.text());
  const edgeCsv = await fetch(withBase("static/relationship-export.csv")).then(res => res.text());

  // 解析 CSV（支持引号内逗号）
  const parseCSV = (text) => {
    const rows = [];
    let row = [];
    let field = "";
    let inQuotes = false;
    const clean = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");

    for (let i = 0; i < clean.length; i++) {
      const char = clean[i];
      const next = clean[i + 1];

      if (char === '"') {
        if (inQuotes && next === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = !inQuotes;
        }
        continue;
      }

      if (char === "," && !inQuotes) {
        row.push(field);
        field = "";
        continue;
      }

      if (char === "\n" && !inQuotes) {
        row.push(field);
        rows.push(row);
        row = [];
        field = "";
        continue;
      }

      field += char;
    }

    if (field.length || row.length) {
      row.push(field);
      rows.push(row);
    }

    if (rows.length === 0) return [];

    const headers = rows[0].map(h => h.trim().replace(/^"|"$/g, ""));

    const normalizeKeys = (rowObj) =>
      Object.fromEntries(
        Object.entries(rowObj).map(([k, v]) => [k.trim().replace(/\s+/g, "_"), v])
      );

    return rows.slice(1).filter(r => r.length > 1).map(values => {
      const rowObj = Object.fromEntries(values.map((v, i) => [headers[i], (v || "").trim().replace(/^"|"$/g, "")]));
      return normalizeKeys(rowObj);
    });
  };

  const rawNodes = parseCSV(nodeCsv);
  const rawEdges = parseCSV(edgeCsv);

  console.log("✅ rawNodes sample:", rawNodes.slice(0, 2));
  console.log("✅ rawEdges sample:", rawEdges.slice(0, 2));

  // 创建节点数据
  const nodes = new vis.DataSet(
    rawNodes.map(n => {
      const zh = n["name_zh"]?.trim() || n["name_zh_simple"]?.trim();
      const sa = n["name_sa"]?.trim();
      const val = n["value"]?.trim();
      const en = n["name_en"]?.trim();

      // 拼接 label：中文优先，其次梵文或值，英文在后缀
      let label = "";
      if (zh || sa || val) {
        label = `${zh || sa || val}${en ? " " + en : ""}`;
      } else if (en) {
        label = en;
      } else {
        label = "Unnamed";
      }

      const title = n["note"]?.trim() || label;

      return {
        id: n["~id"],
        label,
        title,
        color: n["~labels"] === "Number" ? "#3a7bd5" : "#e86e6e",
        cardURL: n["cardURL"]?.trim() || "",
        font: { face: "Georgia" },
        size: 18
      };
    })
  );

  // 创建边数据
  const edges = new vis.DataSet(
    rawEdges.map(e => ({
      from: e["~start_node_id"],
      to: e["~end_node_id"],
      arrows: "to",
      label: e["~relationship_type"] || "",
      font: { align: "middle", face: "Georgia", ital: true, size: 9 },
      color: { color: "#bbb", highlight: "#444" }
    }))
  );

  // 渲染图
  const container = document.getElementById("graph-container");
  const data = { nodes, edges };
  const options = {
    layout: { improvedLayout: true },
    nodes: {
      shape: "dot",
      size: 18,
      font: {
        face: "Georgia",
        size: 13,
        color: "#3b2f22",
        bold: { size: 13, color: "#3b2f22", face: "Georgia" }
      }
    },
    edges: {
      smooth: true,
      font: {
        face: "Georgia",
        size: 9,
        color: "#5a4b3a",
        bold: { size: 9, color: "#5a4b3a", face: "Georgia" }
      }
    },
    interaction: {
      hover: true
    },
    physics: {
      enabled: true,
      stabilization: false,
      minVelocity: 0.02,
      barnesHut: {
        gravitationalConstant: -800,
        springLength: 140,
        springConstant: 0.03,
        damping: 0.18
      },
      adaptiveTimestep: true
    }
  };

  const network = new vis.Network(container, data, options);

  // Zoom controls
  document.getElementById("zoomIn")?.addEventListener("click", () => {
    const scale = network.getScale();
    network.moveTo({ scale: scale * 1.15 });
  });

  document.getElementById("zoomOut")?.addEventListener("click", () => {
    const scale = network.getScale();
    network.moveTo({ scale: scale / 1.15 });
  });

  const baseSizes = new Map();
  nodes.forEach(n => baseSizes.set(n.id, n.size || 18));

  // Subtle ripple response on mouse move (nearest node/edge)
  let lastRipple = 0;
  const baseEdgeWidth = 1;
  network.on("mousemove", (params) => {
    const now = Date.now();
    if (now - lastRipple < 120) return;
    const nodeId = network.getNodeAt(params.pointer.DOM);
    const edgeId = network.getEdgeAt(params.pointer.DOM);
    if (!nodeId && !edgeId) return;
    lastRipple = now;
    if (nodeId) {
      const pos = network.getPositions([nodeId])[nodeId];
      if (pos) {
        network.moveNode(nodeId, pos.x + 8, pos.y - 8);
        setTimeout(() => network.moveNode(nodeId, pos.x, pos.y), 260);
      }
    }
    if (edgeId) {
      edges.update({ id: edgeId, width: baseEdgeWidth + 1, color: { color: "#a88b63" } });
      setTimeout(() => edges.update({ id: edgeId, width: baseEdgeWidth, color: { color: "#bbb" } }), 220);
    }
  });

  network.on("hoverEdge", (params) => {
    edges.update({ id: params.edge, width: baseEdgeWidth + 1.2, color: { color: "#a88b63" } });
  });

  network.on("blurEdge", (params) => {
    edges.update({ id: params.edge, width: baseEdgeWidth, color: { color: "#bbb" } });
  });

  // No idle drift
}

drawGraph();
</script>
