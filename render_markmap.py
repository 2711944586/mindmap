"""render_markmap.py — 从 .mm.md 源文件生成高质量 Markmap HTML 思维导图。

用法:  python render_markmap.py           # 生成全部页面
       python render_markmap.py --serve   # 生成后启动 HTTP 预览

输出:  literature_review.html, research_journey.html, index.html（着陆页）
依赖:  纯 Python 3.9+，无第三方库。HTML 通过 markmap-autoloader 自动加载运行时。
"""
from __future__ import annotations

import argparse
import html
import http.server
import functools
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ── 页面元数据 ──────────────────────────────────────────────
PAGES: dict[str, dict[str, str]] = {
    "literature_review": {
        "title": "文献综述图谱",
        "subtitle": "推荐曝光 · 结构外部性 · 受约束治理",
        "icon": "📚",
        "gradient_from": "#6366f1",
        "gradient_to": "#a855f7",
    },
    "research_journey": {
        "title": "论文研究图谱",
        "subtitle": "对象层次 · 三组件框架 · 理论边界 · 评估协议",
        "icon": "🧭",
        "gradient_from": "#0891b2",
        "gradient_to": "#06b6d4",
    },
}


# ── 思维导图页面模板 ──────────────────────────────────────
PAGE_TEMPLATE = textwrap.dedent("""\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title} — 推荐曝光结构外部性研究</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet"/>
<style>
/* ═══════════════ 全局变量 ═══════════════ */
:root {{
  --g-from: {gradient_from};
  --g-to: {gradient_to};
  --bg: #f0f4f8;
  --fg: #1e293b;
  --surface: rgba(255,255,255,.82);
  --surface-solid: #ffffff;
  --border: rgba(148,163,184,.18);
  --shadow-sm: 0 2px 8px rgba(15,23,42,.04);
  --shadow-md: 0 8px 24px rgba(15,23,42,.06);
  --shadow-lg: 0 20px 50px rgba(15,23,42,.1);
  --radius: 14px;
  --radius-sm: 10px;
  --font: "Inter","Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
  --transition: .3s cubic-bezier(.4,0,.2,1);
}}
[data-theme="dark"] {{
  --bg: #0c1222;
  --fg: #e2e8f0;
  --surface: rgba(30,41,59,.78);
  --surface-solid: #1e293b;
  --border: rgba(71,85,105,.4);
  --shadow-sm: 0 2px 8px rgba(0,0,0,.2);
  --shadow-md: 0 8px 24px rgba(0,0,0,.25);
  --shadow-lg: 0 20px 50px rgba(0,0,0,.4);
}}

/* ═══════════════ 重置 ═══════════════ */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; overflow: hidden; }}
body {{
  font-family: var(--font);
  background: var(--bg);
  color: var(--fg);
  transition: background var(--transition), color var(--transition);
}}

/* ═══════════════ 背景装饰 ═══════════════ */
body::before {{
  content: '';
  position: fixed;
  top: -40%; right: -20%;
  width: 80vw; height: 80vw;
  border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--g-from) 12%, transparent) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}}
body::after {{
  content: '';
  position: fixed;
  bottom: -30%; left: -15%;
  width: 60vw; height: 60vw;
  border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--g-to) 10%, transparent) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}}

/* ═══════════════ 思维导图画布 ═══════════════ */
.markmap {{
  position: absolute;
  top: 0; left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 1;
}}
.markmap svg {{
  width: 100%;
  height: 100%;
}}

/* ═══════════════ 顶部工具栏 ═══════════════ */
.toolbar {{
  position: fixed;
  top: 16px; left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 100px;
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
  box-shadow: var(--shadow-md);
  z-index: 200;
  transition: all var(--transition);
}}
.toolbar:hover {{
  box-shadow: var(--shadow-lg);
}}

/* 品牌标识 */
.brand {{
  display: flex;
  align-items: center;
  gap: 8px;
  padding-right: 12px;
  border-right: 1px solid var(--border);
  margin-right: 4px;
  text-decoration: none;
  color: var(--fg);
}}
.brand-icon {{
  width: 28px; height: 28px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--g-from), var(--g-to));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  box-shadow: 0 2px 8px color-mix(in srgb, var(--g-from) 30%, transparent);
}}
.brand-text {{
  font-size: 13px;
  font-weight: 700;
  letter-spacing: -.01em;
}}
.brand-sub {{
  font-size: 10px;
  font-weight: 500;
  opacity: .5;
}}

/* 按钮 */
.tbtn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  height: 34px;
  min-width: 34px;
  padding: 0 12px;
  border: 1px solid transparent;
  border-radius: 100px;
  background: transparent;
  color: var(--fg);
  font-family: var(--font);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all .2s;
  white-space: nowrap;
}}
.tbtn:hover {{
  background: color-mix(in srgb, var(--g-from) 8%, transparent);
  border-color: color-mix(in srgb, var(--g-from) 15%, transparent);
}}
.tbtn:active {{
  transform: scale(.96);
}}
.tbtn svg {{
  width: 16px; height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}}
.tbtn-icon {{
  padding: 0;
  width: 34px;
}}

/* 搜索 */
.search {{
  display: flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 12px;
  border: 1px solid transparent;
  border-radius: 100px;
  background: color-mix(in srgb, var(--fg) 4%, transparent);
  transition: all .2s;
}}
.search:focus-within {{
  background: var(--surface-solid);
  border-color: var(--g-from);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--g-from) 12%, transparent);
}}
.search svg {{
  width: 14px; height: 14px;
  fill: none; stroke: currentColor;
  stroke-width: 2; opacity: .4;
}}
.search input {{
  border: none;
  background: transparent;
  outline: none;
  font-family: var(--font);
  font-size: 12px;
  color: var(--fg);
  width: 120px;
}}
.search input::placeholder {{ color: color-mix(in srgb, var(--fg) 35%, transparent); }}

/* 分隔符 */
.sep {{
  width: 1px;
  height: 20px;
  background: var(--border);
  margin: 0 4px;
}}

/* ═══════════════ 底部统计 ═══════════════ */
.stats {{
  position: fixed;
  bottom: 20px; left: 20px;
  display: flex; gap: 6px;
  z-index: 200;
}}
.stat {{
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: 100px;
  font-size: 11px;
  font-weight: 600;
  background: var(--surface);
  border: 1px solid var(--border);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: var(--shadow-sm);
}}
.stat-dot {{
  width: 6px; height: 6px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--g-from), var(--g-to));
}}

/* ═══════════════ 响应式 ═══════════════ */
@media (max-width: 768px) {{
  .toolbar {{ top: 10px; padding: 6px 10px; gap: 4px; max-width: calc(100vw - 20px); flex-wrap: wrap; justify-content: center; }}
  .brand {{ display: none; }}
  .search input {{ width: 80px; }}
  .tbtn span {{ display: none; }}
  .stats {{ left: 10px; bottom: 10px; }}
}}

/* ═══════════════ 打印 ═══════════════ */
@media print {{
  .toolbar, .stats {{ display: none !important; }}
  body::before, body::after {{ display: none; }}
}}

/* ═══════════════ markmap 节点文字 ═══════════════ */
.markmap-node text {{
  font-family: var(--font) !important;
}}
</style>
</head>
<body>

<!-- ── 工具栏 ── -->
<div class="toolbar">
  <a class="brand" href="index.html" title="返回首页">
    <div class="brand-icon">{icon}</div>
    <div>
      <div class="brand-text">{title}</div>
      <div class="brand-sub">{subtitle}</div>
    </div>
  </a>

  <div class="search">
    <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    <input id="searchInput" type="text" placeholder="搜索节点…"/>
  </div>

  <div class="sep"></div>

  <button class="tbtn" id="btnExpand" title="展开全部">
    <svg viewBox="0 0 24 24"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
    <span>展开</span>
  </button>
  <button class="tbtn" id="btnCollapse" title="收起">
    <svg viewBox="0 0 24 24"><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="14" y1="10" x2="21" y2="3"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
    <span>收起</span>
  </button>

  <div class="sep"></div>

  <button class="tbtn tbtn-icon" id="btnZoomIn" title="放大">
    <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
  </button>
  <button class="tbtn tbtn-icon" id="btnZoomOut" title="缩小">
    <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
  </button>
  <button class="tbtn tbtn-icon" id="btnFit" title="适配画面">
    <svg viewBox="0 0 24 24"><path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3"/></svg>
  </button>

  <div class="sep"></div>

  <button class="tbtn tbtn-icon" id="btnDark" title="主题切换">
    <svg id="iconSun" viewBox="0 0 24 24" style="display:none"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
    <svg id="iconMoon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>
  </button>
  <button class="tbtn tbtn-icon" id="btnFS" title="全屏">
    <svg viewBox="0 0 24 24"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
  </button>
</div>

<!-- ── 思维导图 ── -->
<div class="markmap">
<script type="text/template">
---
markmap:
  initialExpandLevel: 2
  maxWidth: 380
  colorFreezeLevel: 3
---

{markdown_content}

</script>
</div>

<!-- ── 统计 ── -->
<div class="stats">
  <div class="stat"><span class="stat-dot"></span><span id="sNodes">–</span></div>
  <div class="stat"><span class="stat-dot"></span><span id="sDepth">–</span></div>
</div>

<!-- ── markmap autoloader ── -->
<script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@latest"></script>

<script>
(() => {{
  /* ── 等待 markmap 渲染完成 ── */
  const waitForMM = (cb, tries = 0) => {{
    /* autoloader 在 .markmap 的子 SVG 上挂载实例 */
    const el = document.querySelector('.markmap');
    const svg = el && el.querySelector('svg');
    const mm = svg && (svg.markmap || svg.__markmap__);
    /* 也检查全局 */
    const mmGlobal = window.markmap;
    if (mm && mm.state && mm.state.data) {{
      cb(mm, svg); return;
    }}
    /* 备选：检查 SVG 是否已有子元素（渲染完成标志） */
    if (svg && svg.querySelector('g') && svg.querySelector('g').children.length > 2) {{
      /* 无直接实例引用，用轮询 DOM 操作替代 */
      cb(null, svg); return;
    }}
    if (tries < 100) setTimeout(() => waitForMM(cb, tries + 1), 200);
  }};

  waitForMM((mm, svg) => {{
    if (!mm) {{
      /* 没有获取到实例引用，按钮暂不绑定 */
      console.log('Markmap rendered but instance not accessible');
      return;
    }}

    /* ── 统计 ── */
    let nc = 0, md = 0;
    const walk = (n, d) => {{ nc++; if (d > md) md = d; (n.children||[]).forEach(c => walk(c, d+1)); }};
    if (mm.state && mm.state.data) walk(mm.state.data, 0);
    document.getElementById('sNodes').textContent = nc + ' 节点';
    document.getElementById('sDepth').textContent = md + ' 层';

    /* ── 克隆树 + 遍历 ── */
    const cloneTree = (n) => ({{ ...n, payload: n.payload ? {{ ...n.payload }} : {{}}, children: (n.children||[]).map(cloneTree) }});
    const walkSet = (n, d, fn) => {{ fn(n, d); (n.children||[]).forEach(c => walkSet(c, d+1, fn)); }};

    /* ── 展开/收起 ── */
    document.getElementById('btnExpand').addEventListener('click', async () => {{
      const r = cloneTree(mm.state.data);
      walkSet(r, 0, (n) => {{ n.payload = {{ ...(n.payload||{{}}), fold: 0 }}; }});
      await mm.setData(r); await mm.fit();
    }});
    document.getElementById('btnCollapse').addEventListener('click', async () => {{
      const r = cloneTree(mm.state.data);
      walkSet(r, 0, (n, d) => {{ n.payload = {{ ...(n.payload||{{}}), fold: d >= 2 ? 1 : 0 }}; }});
      await mm.setData(r); await mm.fit();
    }});

    /* ── 缩放 ── */
    document.getElementById('btnZoomIn').addEventListener('click', () => {{
      mm.rescale(1.25);
    }});
    document.getElementById('btnZoomOut').addEventListener('click', () => {{
      mm.rescale(0.8);
    }});
    document.getElementById('btnFit').addEventListener('click', () => {{
      mm.fit();
    }});

    /* ── 搜索 ── */
    let timer;
    document.getElementById('searchInput').addEventListener('input', (e) => {{
      clearTimeout(timer);
      timer = setTimeout(() => {{
        const q = e.target.value.trim().toLowerCase();
        svg.querySelectorAll('text').forEach(t => {{
          const match = q && t.textContent.toLowerCase().includes(q);
          t.style.fill = match ? 'var(--g-from)' : '';
          t.style.fontWeight = match ? '800' : '';
          t.style.fontSize = match ? '1.1em' : '';
        }});
      }}, 200);
    }});
  }});

  /* ── 深色模式 ── */
  const apply = (dark) => {{
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    document.getElementById('iconSun').style.display = dark ? 'block' : 'none';
    document.getElementById('iconMoon').style.display = dark ? 'none' : 'block';
    localStorage.setItem('mm-theme', dark ? 'dark' : 'light');
  }};
  const saved = localStorage.getItem('mm-theme');
  apply(saved === 'dark' || (!saved && matchMedia('(prefers-color-scheme:dark)').matches));
  document.getElementById('btnDark').addEventListener('click', () => {{
    apply(document.documentElement.getAttribute('data-theme') !== 'dark');
  }});

  /* ── 全屏 ── */
  document.getElementById('btnFS').addEventListener('click', () => {{
    document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
  }});
}})();
</script>
</body>
</html>
""")


# ── 着陆页模板 ──────────────────────────────────────────
INDEX_TEMPLATE = textwrap.dedent("""\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>推荐曝光结构外部性研究导图</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;700;900&display=swap" rel="stylesheet"/>
<style>
:root {
  --bg: #f0f4f8; --fg: #1e293b; --surface: #fff; --border: rgba(148,163,184,.15);
  --shadow: 0 8px 30px rgba(15,23,42,.06); --font: "Inter","Noto Sans SC",system-ui,sans-serif;
}
@media (prefers-color-scheme:dark) {
  :root { --bg: #0c1222; --fg: #e2e8f0; --surface: #1e293b; --border: rgba(71,85,105,.4);
           --shadow: 0 8px 30px rgba(0,0,0,.3); }
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { height: 100%; }
body {
  font-family: var(--font); background: var(--bg); color: var(--fg);
  min-height: 100vh; display: flex; flex-direction: column;
  align-items: center; justify-content: center; padding: 40px 20px;
  position: relative; overflow: hidden;
}
/* 装饰光晕 */
body::before {
  content: '';
  position: absolute; top: -30%; left: -20%;
  width: 70vw; height: 70vw; border-radius: 50%;
  background: radial-gradient(circle, rgba(99,102,241,.12) 0%, transparent 70%);
  pointer-events: none;
}
body::after {
  content: '';
  position: absolute; bottom: -25%; right: -15%;
  width: 55vw; height: 55vw; border-radius: 50%;
  background: radial-gradient(circle, rgba(8,145,178,.1) 0%, transparent 70%);
  pointer-events: none;
}
.content { position: relative; z-index: 1; text-align: center; }
h1 { font-size: 2.8rem; font-weight: 900; letter-spacing: -.04em; margin-bottom: 8px;
     background: linear-gradient(135deg, #6366f1, #a855f7, #0891b2);
     -webkit-background-clip: text; -webkit-text-fill-color: transparent;
     background-clip: text; }
.subtitle { font-size: 1rem; opacity: .55; margin-bottom: 56px; font-weight: 500; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 24px; width: 100%; max-width: 820px; }
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 24px; padding: 36px 32px; text-decoration: none; color: var(--fg);
  transition: transform .3s cubic-bezier(.4,0,.2,1), box-shadow .3s;
  box-shadow: var(--shadow); position: relative; overflow: hidden;
}
.card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
  background: var(--card-gradient); opacity: 0; transition: opacity .3s;
}
.card:hover { transform: translateY(-6px); box-shadow: 0 20px 50px rgba(15,23,42,.12); }
.card:hover::before { opacity: 1; }
.card-icon {
  width: 52px; height: 52px; border-radius: 16px;
  background: var(--card-gradient);
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; margin-bottom: 20px;
  box-shadow: 0 4px 12px color-mix(in srgb, var(--card-from) 25%, transparent);
}
.card-title { font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; letter-spacing: -.02em; }
.card-desc { font-size: .9rem; opacity: .55; line-height: 1.7; }
.card-arrow {
  position: absolute; bottom: 24px; right: 24px;
  width: 32px; height: 32px; border-radius: 50%;
  background: color-mix(in srgb, var(--fg) 6%, transparent);
  display: flex; align-items: center; justify-content: center;
  transition: background .2s, transform .2s;
}
.card:hover .card-arrow { background: var(--card-gradient); transform: translateX(2px); }
.card-arrow svg { width: 14px; height: 14px; fill: none; stroke: currentColor; stroke-width: 2.5; }
.card:hover .card-arrow svg { stroke: #fff; }
.footer { margin-top: 56px; font-size: .8rem; opacity: .35; font-weight: 500; }
.footer a { color: inherit; text-decoration: underline; text-underline-offset: 2px; }
@media (max-width: 768px) { h1 { font-size: 2rem; } .cards { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="content">
<h1>结构外部性研究导图</h1>
<p class="subtitle">推荐曝光分配 · 结构外部性 · 审计与治理</p>
<div class="cards">
{cards_html}
</div>
<p class="footer">基于 <a href="https://markmap.js.org/" target="_blank">Markmap</a> 构建 · 源码托管于 <a href="https://github.com/2711944586/mindmap" target="_blank">GitHub</a></p>
</div>
</body>
</html>
""")

CARD_TEMPLATE = textwrap.dedent("""\
<a class="card" href="{stem}.html" style="--card-gradient: linear-gradient(135deg, {gradient_from}, {gradient_to}); --card-from: {gradient_from};">
  <div class="card-icon">{icon}</div>
  <div class="card-title">{title}</div>
  <div class="card-desc">{subtitle}</div>
  <div class="card-arrow"><svg viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg></div>
</a>
""")


# ── 核心渲染逻辑 ──────────────────────────────────────────
def render_page(stem: str, meta: dict[str, str]) -> None:
    md_path = ROOT / f"{stem}.mm.md"
    html_path = ROOT / f"{stem}.html"
    if not md_path.exists():
        print(f"[SKIP] {md_path.name} not found")
        return

    md_content = md_path.read_text(encoding="utf-8")
    # HTML 转义 markdown 内容以安全嵌入 <div>
    md_escaped = html.escape(md_content, quote=False)
    # 恢复 markdown 结构字符
    md_escaped = md_escaped.replace("&amp;", "&")

    page_html = PAGE_TEMPLATE.format(
        title=meta["title"],
        subtitle=meta["subtitle"],
        icon=meta["icon"],
        gradient_from=meta["gradient_from"],
        gradient_to=meta["gradient_to"],
        markdown_content=md_content,  # autoloader 需要原始 markdown
    )
    html_path.write_text(page_html, encoding="utf-8")
    print(f"[OK] {html_path.name}  ({md_path.stat().st_size:,} bytes → {html_path.stat().st_size:,} bytes)")


def render_index() -> None:
    cards = "\n".join(
        CARD_TEMPLATE.format(stem=stem, **meta)
        for stem, meta in PAGES.items()
    )
    index_html = INDEX_TEMPLATE.replace("{cards_html}", cards)
    out = ROOT / "index.html"
    out.write_text(index_html, encoding="utf-8")
    print(f"[OK] {out.name}")


def serve(port: int = 8080) -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    with http.server.HTTPServer(("", port), handler) as srv:
        print(f"\n  🌐 预览: http://localhost:{port}/index.html\n  Ctrl+C 停止\n")
        srv.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="渲染 Markmap 思维导图")
    parser.add_argument("--serve", action="store_true", help="生成后启动 HTTP 预览")
    parser.add_argument("--port", type=int, default=8080, help="预览端口 (默认 8080)")
    args = parser.parse_args()

    for stem, meta in PAGES.items():
        render_page(stem, meta)
    render_index()

    if args.serve:
        serve(args.port)


if __name__ == "__main__":
    main()
