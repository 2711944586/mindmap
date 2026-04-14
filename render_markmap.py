"""render_markmap.py — 从 .mm.md 源文件生成交互式 Markmap HTML 页面。

用法:
  python render_markmap.py
  python render_markmap.py --serve

输出:
  literature_review.html
  research_journey.html
  index.html
"""
from __future__ import annotations

import argparse
import functools
import html
import http.server
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PAGES: dict[str, dict[str, str]] = {
    "literature_review": {
        "title": "文献综述图谱",
        "subtitle": "推荐曝光 · 结构外部性 · 证据与治理",
        "label": "Literature Map",
        "accent": "#9a5d2f",
        "accent_soft": "#d0b38f",
        "index_chip": "01",
    },
    "research_journey": {
        "title": "研究思考图谱",
        "subtitle": "对象层次 · 三组件框架 · 评估协议 · 边界",
        "label": "Research Journey",
        "accent": "#215f5a",
        "accent_soft": "#93bdb6",
        "index_chip": "02",
    },
}


PAGE_TEMPLATE = textwrap.dedent(
    """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Manrope:wght@500;600;700;800&family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@500;700&display=swap" rel="stylesheet"/>
<style>
:root {{
  --bg: #efe4d2;
  --bg-deep: #f7f1e7;
  --surface: rgba(252, 249, 243, 0.88);
  --surface-strong: rgba(255, 253, 249, 0.94);
  --line: rgba(70, 49, 31, 0.14);
  --text: #23180f;
  --text-soft: #685a4b;
  --shadow: 0 18px 50px rgba(49, 34, 19, 0.12);
  --chip: {accent};
  --chip-soft: {accent_soft};
  --node-0: #2b2117;
  --node-1: #7c4f29;
  --node-2: #8f6c45;
  --node-3: #4f6454;
  --node-4: #49606e;
  --ui-font: "Manrope", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  --map-font: "Fraunces", "Noto Serif SC", "Source Han Serif SC", serif;
  --match: #b56d32;
}}

html[data-theme="nocturne"] {{
  --bg: #12181d;
  --bg-deep: #1b242a;
  --surface: rgba(19, 26, 31, 0.82);
  --surface-strong: rgba(24, 31, 37, 0.9);
  --line: rgba(184, 206, 212, 0.16);
  --text: #e5ecef;
  --text-soft: #a9b8be;
  --shadow: 0 18px 50px rgba(0, 0, 0, 0.34);
  --chip: {accent_soft};
  --chip-soft: {accent};
  --node-0: #edf3f5;
  --node-1: #a9d1ca;
  --node-2: #d5bea0;
  --node-3: #b6c2d4;
  --node-4: #d5d1ca;
  --ui-font: "Manrope", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  --map-font: "Manrope", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  --match: #f1c28b;
}}

*,
*::before,
*::after {{
  box-sizing: border-box;
}}

html,
body {{
  width: 100%;
  height: 100%;
  overflow: hidden;
}}

body {{
  margin: 0;
  color: var(--text);
  font-family: var(--ui-font);
  background:
    radial-gradient(circle at 12% 8%, color-mix(in srgb, var(--chip-soft) 24%, transparent), transparent 28%),
    radial-gradient(circle at 92% 16%, color-mix(in srgb, var(--chip) 14%, transparent), transparent 24%),
    linear-gradient(180deg, var(--bg-deep) 0%, var(--bg) 100%);
}}

body::before {{
  content: "";
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px);
  background-size: 40px 40px;
  opacity: 0.16;
  pointer-events: none;
}}

#mindmap {{
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}}

#mindmap svg {{
  width: 100%;
  height: 100%;
}}

.dock {{
  position: fixed;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  width: min(1100px, calc(100vw - 24px));
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: var(--surface);
  backdrop-filter: blur(18px) saturate(1.05);
  -webkit-backdrop-filter: blur(18px) saturate(1.05);
  box-shadow: var(--shadow);
}}

.brand {{
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}}

.brand-mark {{
  width: 38px;
  height: 38px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--chip) 30%, var(--line));
  background: linear-gradient(135deg, color-mix(in srgb, var(--chip) 92%, white 8%), color-mix(in srgb, var(--chip-soft) 78%, white 22%));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fffaf2;
  font: 800 12px/1 var(--ui-font);
  letter-spacing: 0.06em;
}}

.brand-copy {{
  min-width: 0;
}}

.brand-label {{
  font: 700 11px/1 var(--ui-font);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-soft);
  margin-bottom: 5px;
}}

.brand-title {{
  font: 700 18px/1.1 var(--map-font);
  letter-spacing: -0.02em;
}}

.brand-subtitle {{
  font: 600 11px/1.35 var(--ui-font);
  color: var(--text-soft);
  margin-top: 4px;
}}

.controls {{
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}}

.search-box {{
  display: flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: color-mix(in srgb, var(--surface-strong) 92%, transparent);
}}

.search-box svg,
.tool-btn svg {{
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}}

.search-box input {{
  width: 120px;
  border: 0;
  outline: none;
  padding: 0;
  background: transparent;
  color: var(--text);
  font: 600 12px/1 var(--ui-font);
}}

.search-box input::placeholder {{
  color: color-mix(in srgb, var(--text-soft) 80%, white 20%);
}}

.tool-btn {{
  height: 38px;
  min-width: 38px;
  padding: 0 14px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: color-mix(in srgb, var(--surface-strong) 90%, transparent);
  color: var(--text);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font: 700 12px/1 var(--ui-font);
  transition: transform .14s ease, background .14s ease, border-color .14s ease;
}}

.tool-btn:hover {{
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--chip) 42%, var(--line));
  background: color-mix(in srgb, var(--chip-soft) 18%, var(--surface-strong));
}}

.tool-btn:active {{
  transform: translateY(0);
}}

.tool-btn.compact {{
  padding: 0;
  width: 38px;
}}

.theme-btn .theme-name {{
  display: inline-block;
  min-width: 62px;
  text-align: left;
}}

.status-panel {{
  position: fixed;
  left: 18px;
  bottom: 18px;
  z-index: 20;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}}

.status-pill {{
  min-height: 34px;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--surface);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: var(--shadow);
  color: var(--text-soft);
  font: 700 11px/1 var(--ui-font);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}}

.status-dot {{
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--chip), var(--chip-soft));
}}

.theme-note {{
  position: fixed;
  right: 18px;
  bottom: 18px;
  z-index: 20;
  max-width: min(280px, calc(100vw - 36px));
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid var(--line);
  background: var(--surface);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: var(--shadow);
}}

.theme-note .theme-note-title {{
  font: 700 11px/1 var(--ui-font);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-soft);
  margin-bottom: 6px;
}}

.theme-note .theme-note-body {{
  font: 700 13px/1.45 var(--map-font);
}}

.markmap-node > circle {{
  stroke: color-mix(in srgb, var(--chip) 34%, var(--line));
  stroke-width: 1.25px;
}}

.markmap-node text {{
  font-family: var(--map-font) !important;
  letter-spacing: 0.01em;
}}

.mm-match {{
  fill: var(--match) !important;
  font-weight: 800 !important;
}}

@media (max-width: 900px) {{
  .dock {{
    top: 12px;
    padding: 10px;
    align-items: stretch;
    flex-direction: column;
  }}

  .brand {{
    width: 100%;
  }}

  .controls {{
    width: 100%;
    justify-content: flex-start;
  }}
}}

@media (max-width: 640px) {{
  .brand-title {{
    font-size: 16px;
  }}

  .brand-subtitle {{
    display: none;
  }}

  .search-box input {{
    width: 88px;
  }}

  .tool-btn span {{
    display: none;
  }}

  .theme-btn .theme-name {{
    display: none;
  }}

  .theme-note {{
    display: none;
  }}
}}

@media print {{
  .dock,
  .status-panel,
  .theme-note {{
    display: none !important;
  }}

  body::before {{
    display: none;
  }}
}}
</style>
</head>
<body>
<div id="mindmap"></div>

<section class="dock">
  <div class="brand">
    <div class="brand-mark">{index_chip}</div>
    <div class="brand-copy">
      <div class="brand-label">{label}</div>
      <div class="brand-title">{heading}</div>
      <div class="brand-subtitle">{subtitle}</div>
    </div>
  </div>

  <div class="controls">
    <label class="search-box" for="searchInput" title="搜索节点">
      <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><line x1="16.65" y1="16.65" x2="21" y2="21"/></svg>
      <input id="searchInput" type="text" placeholder="搜索节点"/>
    </label>

    <button class="tool-btn" id="expandBtn" title="展开全部">
      <svg viewBox="0 0 24 24"><polyline points="7 10 12 15 17 10"/><polyline points="7 4 12 9 17 4"/></svg>
      <span>展开全部</span>
    </button>

    <button class="tool-btn" id="resetBtn" title="恢复初始状态">
      <svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 3-6.7"/><polyline points="3 3 3 9 9 9"/></svg>
      <span>恢复初始</span>
    </button>

    <button class="tool-btn compact" id="zoomInBtn" title="放大">
      <svg viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5"/><line x1="21" y1="21" x2="15.5" y2="15.5"/><line x1="10.5" y1="7.5" x2="10.5" y2="13.5"/><line x1="7.5" y1="10.5" x2="13.5" y2="10.5"/></svg>
    </button>

    <button class="tool-btn compact" id="zoomOutBtn" title="缩小">
      <svg viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5"/><line x1="21" y1="21" x2="15.5" y2="15.5"/><line x1="7.5" y1="10.5" x2="13.5" y2="10.5"/></svg>
    </button>

    <button class="tool-btn compact" id="fitBtn" title="适配画面">
      <svg viewBox="0 0 24 24"><path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M16 3h3a2 2 0 0 1 2 2v3"/><path d="M8 21H5a2 2 0 0 1-2-2v-3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/></svg>
    </button>

    <button class="tool-btn theme-btn" id="themeBtn" title="切换主题">
      <svg viewBox="0 0 24 24"><path d="M21 12.6A8.6 8.6 0 1 1 11.4 3a7 7 0 0 0 9.6 9.6Z"/></svg>
      <span class="theme-name" id="themeName">Paper</span>
    </button>

    <button class="tool-btn compact" id="fullscreenBtn" title="全屏">
      <svg viewBox="0 0 24 24"><path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M16 3h3a2 2 0 0 1 2 2v3"/><path d="M8 21H5a2 2 0 0 1-2-2v-3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/></svg>
    </button>
  </div>
</section>

<section class="status-panel">
  <div class="status-pill"><span class="status-dot"></span><span id="nodeCount">- 节点</span></div>
  <div class="status-pill"><span class="status-dot"></span><span id="depthCount">- 层</span></div>
</section>

<section class="theme-note">
  <div class="theme-note-title">Theme</div>
  <div class="theme-note-body" id="themeNoteBody">Paper theme uses serif labels and a warmer page surface.</div>
</section>

<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script src="https://unpkg.com/markmap-view@0.18.12/dist/browser/index.js"></script>
<script src="https://unpkg.com/markmap-lib@0.18.12/dist/browser/index.iife.js"></script>
<script>
;(async () => {{
  const runtime = window.markmap;
  if (!runtime) return;
  const {{ Transformer, Markmap, loadCSS, loadJS }} = runtime;
  const markdown = {markdown_json};
  const transformer = new Transformer();
  const result = transformer.transform(markdown);
  const root = result.root;
  const features = result.features;

  if (loadCSS || loadJS) {{
    const assets = transformer.getUsedAssets(features);
    if (assets.styles && loadCSS) loadCSS(assets.styles);
    if (assets.scripts && loadJS) {{
      await loadJS(assets.scripts, {{ getMarkmap: () => window.markmap }});
    }}
  }}

  const clone = (value) => JSON.parse(JSON.stringify(value));
  const initialRoot = clone(root);

  const themeMeta = {{
    paper: {{
      name: "Paper",
      note: "Paper theme uses serif labels and a warmer page surface.",
      palette: ["#2b2117", "#7c4f29", "#8f6c45", "#4f6454", "#49606e"],
      font: '"Fraunces", "Noto Serif SC", serif',
    }},
    nocturne: {{
      name: "Nocturne",
      note: "Nocturne theme shifts to cleaner sans labels and a darker studio palette.",
      palette: ["#edf3f5", "#a9d1ca", "#d5bea0", "#b6c2d4", "#d5d1ca"],
      font: '"Manrope", "Noto Sans SC", sans-serif',
    }},
  }};

  const preferredDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  let currentTheme = localStorage.getItem("mindmap-theme") || (preferredDark ? "nocturne" : "paper");
  document.documentElement.dataset.theme = currentTheme;

  const nodeColor = (node) => {{
    const palette = themeMeta[currentTheme].palette;
    const depth = node.state && typeof node.state.depth === "number" ? node.state.depth : 0;
    return palette[depth % palette.length];
  }};

  const mm = Markmap.create("#mindmap", {{
    autoFit: true,
    duration: 120,
    maxWidth: 280,
    paddingX: 18,
    spacingVertical: 6,
    initialExpandLevel: 2,
    color: nodeColor,
    lineWidth: (node) => Math.max(1.1, 2.4 - ((node.state && node.state.depth) || 0) * 0.28),
  }}, clone(initialRoot));

  const applyTextFont = () => {{
    const font = themeMeta[currentTheme].font;
    document.querySelectorAll("#mindmap text").forEach((text) => {{
      text.style.fontFamily = font;
    }});
  }};

  const applyTheme = () => {{
    document.documentElement.dataset.theme = currentTheme;
    document.getElementById("themeName").textContent = themeMeta[currentTheme].name;
    document.getElementById("themeNoteBody").textContent = themeMeta[currentTheme].note;
    localStorage.setItem("mindmap-theme", currentTheme);
    mm.setOptions({{ color: nodeColor }});
    mm.renderData(mm.state.data);
    applyTextFont();
  }};

  const countStats = (node, depth = 0) => {{
    let nodes = 1;
    let maxDepth = depth;
    (node.children || []).forEach((child) => {{
      const result = countStats(child, depth + 1);
      nodes += result.nodes;
      maxDepth = Math.max(maxDepth, result.maxDepth);
    }});
    return {{ nodes, maxDepth }};
  }};

  const stats = countStats(initialRoot, 0);
  document.getElementById("nodeCount").textContent = `${{stats.nodes}} 节点`;
  document.getElementById("depthCount").textContent = `${{stats.maxDepth}} 层`;

  const walk = (node, callback, depth = 0) => {{
    callback(node, depth);
    (node.children || []).forEach((child) => walk(child, callback, depth + 1));
  }};

  document.getElementById("expandBtn").addEventListener("click", async () => {{
    const expanded = clone(initialRoot);
    walk(expanded, (node) => {{
      node.payload = Object.assign({{}}, node.payload || {{}}, {{ fold: 0 }});
    }});
    await mm.setData(expanded);
    mm.fit();
    applyTextFont();
  }});

  document.getElementById("resetBtn").addEventListener("click", async () => {{
    await mm.setData(clone(initialRoot));
    mm.fit();
    applyTextFont();
  }});

  document.getElementById("zoomInBtn").addEventListener("click", () => mm.rescale(1.22));
  document.getElementById("zoomOutBtn").addEventListener("click", () => mm.rescale(0.82));
  document.getElementById("fitBtn").addEventListener("click", () => mm.fit());

  document.getElementById("themeBtn").addEventListener("click", () => {{
    currentTheme = currentTheme === "paper" ? "nocturne" : "paper";
    applyTheme();
  }});

  document.getElementById("fullscreenBtn").addEventListener("click", () => {{
    if (document.fullscreenElement) {{
      document.exitFullscreen();
    }} else {{
      document.documentElement.requestFullscreen();
    }}
  }});

  let searchTimer;
  document.getElementById("searchInput").addEventListener("input", (event) => {{
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {{
      const query = event.target.value.trim().toLowerCase();
      document.querySelectorAll("#mindmap text").forEach((text) => {{
        const match = query && text.textContent.toLowerCase().includes(query);
        text.classList.toggle("mm-match", !!match);
      }});
      applyTextFont();
    }}, 120);
  }});

  applyTheme();
  mm.fit();
  setTimeout(applyTextFont, 80);
}})();
</script>
</body>
</html>
"""
)


INDEX_TEMPLATE = textwrap.dedent(
    """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>推荐曝光结构外部性研究导图</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Manrope:wght@500;600;700;800&family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@500;700&display=swap" rel="stylesheet"/>
<style>
:root {{
  --bg: #efe5d5;
  --bg-deep: #f7f1e8;
  --surface: rgba(255, 252, 247, 0.9);
  --line: rgba(75, 56, 38, 0.12);
  --text: #22170f;
  --text-soft: #6e5d4c;
  --shadow: 0 20px 56px rgba(53, 37, 20, 0.12);
  --sans: "Manrope", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  --serif: "Fraunces", "Noto Serif SC", serif;
}}

@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #141a1f;
    --bg-deep: #1c252b;
    --surface: rgba(24, 31, 37, 0.9);
    --line: rgba(184, 206, 212, 0.12);
    --text: #e6ecef;
    --text-soft: #a9b8be;
    --shadow: 0 20px 56px rgba(0, 0, 0, 0.34);
  }}
}}

*,
*::before,
*::after {{
  box-sizing: border-box;
}}

body {{
  margin: 0;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text);
  background:
    radial-gradient(circle at 16% 14%, rgba(154, 93, 47, 0.18), transparent 24%),
    radial-gradient(circle at 84% 18%, rgba(33, 95, 90, 0.18), transparent 24%),
    linear-gradient(180deg, var(--bg-deep) 0%, var(--bg) 100%);
  font-family: var(--sans);
}}

body::before {{
  content: "";
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px);
  background-size: 42px 42px;
  opacity: 0.14;
  pointer-events: none;
}}

.shell {{
  position: relative;
  z-index: 1;
  width: min(760px, 100%);
}}

.hero {{
  margin-bottom: 26px;
}}

.kicker {{
  font: 700 11px/1 var(--sans);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-soft);
  margin-bottom: 10px;
}}

h1 {{
  margin: 0 0 10px;
  font: 700 clamp(2rem, 5vw, 3.5rem)/0.95 var(--serif);
  letter-spacing: -0.04em;
}}

.lead {{
  max-width: 620px;
  color: var(--text-soft);
  font: 600 14px/1.7 var(--sans);
}}

.cards {{
  display: grid;
  gap: 14px;
}}

.card {{
  display: grid;
  grid-template-columns: 76px 1fr 30px;
  align-items: center;
  gap: 16px;
  padding: 18px 18px;
  border-radius: 22px;
  border: 1px solid var(--line);
  background: var(--surface);
  box-shadow: var(--shadow);
  color: inherit;
  text-decoration: none;
  transition: transform .14s ease, border-color .14s ease, background .14s ease;
}}

.card:hover {{
  transform: translateY(-2px);
}}

.chip {{
  height: 52px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fffaf2;
  font: 800 18px/1 var(--sans);
  letter-spacing: 0.08em;
  border: 1px solid rgba(255,255,255,0.22);
}}

.card-copy {{
  min-width: 0;
}}

.card-label {{
  font: 700 11px/1 var(--sans);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-soft);
  margin-bottom: 6px;
}}

.card-title {{
  font: 700 24px/1.08 var(--serif);
  letter-spacing: -0.03em;
  margin-bottom: 6px;
}}

.card-subtitle {{
  color: var(--text-soft);
  font: 600 13px/1.6 var(--sans);
}}

.arrow {{
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--line);
}}

.arrow svg {{
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
}}

.footer {{
  margin-top: 18px;
  color: var(--text-soft);
  font: 700 11px/1.5 var(--sans);
}}

.footer a {{
  color: inherit;
}}

@media (max-width: 640px) {{
  .card {{
    grid-template-columns: 62px 1fr;
  }}

  .arrow {{
    display: none;
  }}

  .card-title {{
    font-size: 20px;
  }}
}}
</style>
</head>
<body>
<main class="shell">
  <section class="hero">
    <div class="kicker">Interactive Atlas</div>
    <h1>推荐曝光结构外部性研究导图</h1>
    <div class="lead">保留更克制的首页结构与更轻的页面负担，分别进入文献综述图谱和最新论文的 research journey 图谱。</div>
  </section>

  <section class="cards">
    {cards_html}
  </section>

  <div class="footer">基于 <a href="https://markmap.js.org/" target="_blank">Markmap</a> 构建 · 仓库：<a href="https://github.com/2711944586/mindmap" target="_blank">2711944586/mindmap</a></div>
</main>
</body>
</html>
"""
)


CARD_TEMPLATE = textwrap.dedent(
    """\
<a class="card" href="{stem}.html">
  <div class="chip" style="background: linear-gradient(135deg, {accent}, {accent_soft});">{index_chip}</div>
  <div class="card-copy">
    <div class="card-label">{label}</div>
    <div class="card-title">{title}</div>
    <div class="card-subtitle">{subtitle}</div>
  </div>
  <div class="arrow">
    <svg viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
  </div>
</a>
"""
)


def render_page(stem: str, meta: dict[str, str]) -> None:
    markdown_path = ROOT / f"{stem}.mm.md"
    html_path = ROOT / f"{stem}.html"
    if not markdown_path.exists():
        print(f"[SKIP] {markdown_path.name} not found")
        return

    markdown_text = markdown_path.read_text(encoding="utf-8")
    html_text = PAGE_TEMPLATE.format(
        title=html.escape(meta["title"]),
        heading=html.escape(meta["title"]),
        subtitle=html.escape(meta["subtitle"]),
        label=html.escape(meta["label"]),
        accent=meta["accent"],
        accent_soft=meta["accent_soft"],
        index_chip=html.escape(meta["index_chip"]),
        markdown_json=json.dumps(markdown_text, ensure_ascii=False),
    )
    html_path.write_text(html_text, encoding="utf-8")
    print(f"[OK] {html_path.name}  ({markdown_path.stat().st_size:,} bytes → {html_path.stat().st_size:,} bytes)")


def render_index() -> None:
    cards = [
        CARD_TEMPLATE.format(stem=stem, **meta)
        for stem, meta in PAGES.items()
    ]
    index_path = ROOT / "index.html"
    index_path.write_text(INDEX_TEMPLATE.format(cards_html="\n".join(cards)), encoding="utf-8")
    print("[OK] index.html")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    for stem, meta in PAGES.items():
        render_page(stem, meta)
    render_index()

    if args.serve:
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
        with http.server.ThreadingHTTPServer(("", args.port), handler) as server:
            print(f"\n  http://localhost:{args.port}\n")
            server.serve_forever()


if __name__ == "__main__":
    main()
