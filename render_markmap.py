"""render_markmap.py — .mm.md → Markmap HTML

修复目标:
- 保证文献综述与 research journey 页面稳定渲染
- 保留展开、恢复初始、主题切换、搜索与全屏
- 维持较轻的首页与较稳的运行时
"""
from __future__ import annotations

import argparse
import functools
import http.server
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PAGES = {
    "literature_review": {
        "title": "文献综述图谱",
        "sub": "推荐曝光 · 结构外部性 · 受约束治理",
        "icon": "📚",
        "accent": "#4338ca",
    },
    "research_journey": {
        "title": "研究思考图谱",
        "sub": "对象层次 · 三组件框架 · 评估协议 · 解释边界",
        "icon": "🧭",
        "accent": "#0f766e",
    },
}


PAGE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>$TITLE$</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden;font-family:system-ui,-apple-system,"Segoe UI","Noto Sans SC",sans-serif}
body{background:#fafaf9;color:#1c1917;transition:background .15s,color .15s}
body.dark{background:#18181b;color:#e7e5e4}

svg#mm{position:fixed;inset:0;width:100%;height:100%}

svg#mm text{
  font-family:system-ui,-apple-system,"Segoe UI","Noto Sans SC",sans-serif !important;
  font-size:13px !important;
}
body.dark svg#mm text{fill:#d4d4d8 !important}

.bar{
  position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:999;
  display:inline-flex;align-items:center;gap:2px;padding:5px 10px;
  background:rgba(250,250,249,.88);border:1px solid rgba(0,0,0,.07);
  border-radius:10px;backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  box-shadow:0 1px 3px rgba(0,0,0,.04)
}
body.dark .bar{background:rgba(24,24,27,.88);border-color:rgba(255,255,255,.07)}

.bar a.home{
  display:flex;align-items:center;gap:5px;padding:0 8px 0 4px;
  margin-right:6px;border-right:1px solid rgba(0,0,0,.06);
  text-decoration:none;color:inherit;font-size:12px;font-weight:600
}
body.dark .bar a.home{border-right-color:rgba(255,255,255,.06)}
.bar .dot{width:6px;height:6px;border-radius:50%;background:$ACCENT$}

.b{
  display:inline-flex;align-items:center;gap:3px;height:28px;min-width:28px;
  padding:0 8px;border:none;border-radius:7px;background:transparent;
  color:inherit;font:600 11px/1 system-ui,sans-serif;cursor:pointer;transition:background .12s
}
.b:hover{background:rgba(0,0,0,.05)}
body.dark .b:hover{background:rgba(255,255,255,.08)}
.b:active{opacity:.7}
.b svg{width:13px;height:13px;fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
.b.ico{padding:0;width:28px;justify-content:center}

.sep{width:1px;height:14px;background:rgba(0,0,0,.06);margin:0 3px}
body.dark .sep{background:rgba(255,255,255,.06)}

.sf{
  display:flex;align-items:center;gap:4px;height:28px;padding:0 8px;
  border:1px solid rgba(0,0,0,.06);border-radius:7px;transition:border-color .15s
}
body.dark .sf{border-color:rgba(255,255,255,.06)}
.sf:focus-within{border-color:$ACCENT$}
.sf svg{width:11px;height:11px;fill:none;stroke:currentColor;stroke-width:1.5;opacity:.3}
.sf input{border:none;outline:none;font:11px system-ui;color:inherit;width:80px;background:transparent}
body.dark .sf input{color:#e7e5e4}

.badge{position:fixed;bottom:12px;left:12px;z-index:999;display:flex;gap:4px}
.badge span{
  padding:2px 8px;border-radius:6px;font:600 10px/1.6 system-ui;
  background:rgba(250,250,249,.85);border:1px solid rgba(0,0,0,.06);
  backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)
}
body.dark .badge span{background:rgba(24,24,27,.85);border-color:rgba(255,255,255,.06)}

.mm-hl{fill:$ACCENT$ !important;font-weight:700 !important}

@media(max-width:640px){
  .bar{top:6px;padding:4px 6px;gap:1px;max-width:calc(100vw - 12px);flex-wrap:wrap;justify-content:center}
  .bar a.home{display:none}
  .b span{display:none}
  .sf input{width:50px}
}
@media print{.bar,.badge{display:none !important}}
</style>
</head>
<body>

<div class="bar">
  <a class="home" href="index.html"><span class="dot"></span>$TITLE$</a>
  <div class="sf"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><input id="si" placeholder="搜索…"/></div>
  <div class="sep"></div>
  <button class="b" id="bE"><svg viewBox="0 0 24 24"><polyline points="7 13 12 18 17 13"/><polyline points="7 6 12 11 17 6"/></svg><span>展开</span></button>
  <button class="b" id="bC"><svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 3-6.7"/><polyline points="3 3 3 9 9 9"/></svg><span>恢复</span></button>
  <div class="sep"></div>
  <button class="b ico" id="bZI" title="放大"><svg viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5"/><line x1="21" y1="21" x2="15.5" y2="15.5"/><line x1="10.5" y1="7.5" x2="10.5" y2="13.5"/><line x1="7.5" y1="10.5" x2="13.5" y2="10.5"/></svg></button>
  <button class="b ico" id="bZO" title="缩小"><svg viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5"/><line x1="21" y1="21" x2="15.5" y2="15.5"/><line x1="7.5" y1="10.5" x2="13.5" y2="10.5"/></svg></button>
  <button class="b ico" id="bF0" title="适配"><svg viewBox="0 0 24 24"><path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3"/></svg></button>
  <div class="sep"></div>
  <button class="b ico" id="bD" title="切换主题"><svg id="iS" viewBox="0 0 24 24" style="display:none"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41m11.32-11.32l1.41-1.41"/></svg><svg id="iM" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg></button>
  <button class="b ico" id="bFS" title="全屏"><svg viewBox="0 0 24 24"><path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3"/></svg></button>
</div>

<svg id="mm"></svg>

<div class="badge"><span id="sN">–</span><span id="sD">–</span></div>

<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script src="https://cdn.jsdelivr.net/npm/markmap-view"></script>
<script src="https://cdn.jsdelivr.net/npm/markmap-lib"></script>
<script>
(function(){
  var md = $MD$;
  var T = markmap.Transformer ? new markmap.Transformer() : new (markmap.default || markmap).Transformer();
  var r = T.transform(md);
  var root = r.root, features = r.features;
  var MM = markmap.Markmap || (markmap.default || markmap).Markmap;
  if(markmap.loadCSS && features){
    var a = T.getUsedAssets(features);
    if(a.styles) markmap.loadCSS(a.styles);
    if(a.scripts) markmap.loadJS(a.scripts);
  }

  var initial = JSON.parse(JSON.stringify(root));
  var PL = ['#57534e','#64748b','#5b7261','#78716c','#6b7280','#71717a','#57534e','#64748b'];
  var PD = ['#a8a29e','#94a3b8','#86a990','#a8a29e','#9ca3af','#a1a1aa','#a8a29e','#94a3b8'];
  function isDark(){ return document.body.classList.contains('dark'); }
  function colorFn(n){
    var pal = isDark() ? PD : PL;
    return pal[n.state.depth % pal.length];
  }

  var mm = MM.create('#mm', {
    autoFit: true,
    duration: 150,
    maxWidth: 260,
    paddingX: 12,
    spacingVertical: 4,
    initialExpandLevel: 2,
    color: colorFn,
    lineWidth: function(n){ return Math.max(1, 2.2 - n.state.depth * 0.35); }
  }, root);

  var nc = 0, mx = 0;
  function cnt(n,d){ nc++; if(d>mx) mx=d; if(n.children) n.children.forEach(function(c){cnt(c,d+1);}); }
  cnt(initial, 0);
  document.getElementById('sN').textContent = nc + ' 节点';
  document.getElementById('sD').textContent = mx + ' 层';

  function walk(node, fn){
    fn(node);
    if(node.children) node.children.forEach(function(c){ walk(c, fn); });
  }

  function resetView(data){
    mm.setData(data).then(function(){ mm.fit(); });
  }

  document.getElementById('bE').onclick = function(){
    walk(mm.state.data, function(n){
      n.payload = Object.assign({}, n.payload, { fold: 0 });
    });
    mm.renderData(mm.state.data);
    mm.fit();
  };

  document.getElementById('bC').onclick = function(){
    resetView(JSON.parse(JSON.stringify(initial)));
  };

  document.getElementById('bZI').onclick = function(){ mm.rescale(1.25); };
  document.getElementById('bZO').onclick = function(){ mm.rescale(0.8); };
  document.getElementById('bF0').onclick = function(){ mm.fit(); };

  function syncIcons(){
    document.getElementById('iS').style.display = isDark() ? 'block' : 'none';
    document.getElementById('iM').style.display = isDark() ? 'none' : 'block';
  }
  if(localStorage.getItem('mm-t') === 'dark' || matchMedia('(prefers-color-scheme:dark)').matches){
    document.body.classList.add('dark');
  }
  syncIcons();
  document.getElementById('bD').onclick = function(){
    document.body.classList.toggle('dark');
    syncIcons();
    localStorage.setItem('mm-t', isDark() ? 'dark' : 'light');
    mm.setOptions({ color: colorFn });
    mm.renderData(mm.state.data);
  };

  var st;
  document.getElementById('si').oninput = function(){
    clearTimeout(st);
    var self = this;
    st = setTimeout(function(){
      var q = self.value.trim().toLowerCase();
      document.querySelectorAll('#mm text').forEach(function(t){
        t.classList.toggle('mm-hl', q && t.textContent.toLowerCase().indexOf(q) >= 0);
      });
    }, 150);
  };

  document.getElementById('bFS').onclick = function(){
    if(document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen();
  };
})();
</script>
</body>
</html>"""


INDEX_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>推荐曝光结构外部性研究导图</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{
  font-family:system-ui,-apple-system,"Segoe UI","Noto Sans SC",sans-serif;
  background:#fafaf9;color:#1c1917;min-height:100vh;
  display:flex;align-items:center;justify-content:center;padding:48px 24px
}
@media(prefers-color-scheme:dark){
  body{background:#18181b;color:#e7e5e4}
  .card{background:#1c1c1e;border-color:rgba(255,255,255,.06)}
  .card:hover{box-shadow:0 2px 8px rgba(0,0,0,.3)}
}
.w{max-width:520px;width:100%}
h1{font-size:1.7rem;font-weight:800;letter-spacing:-.03em;margin-bottom:6px}
.sub{font-size:.82rem;opacity:.48;margin-bottom:34px;font-weight:500;line-height:1.6}
.cards{display:flex;flex-direction:column;gap:10px}
.card{
  display:flex;align-items:center;gap:14px;padding:16px 20px;
  border:1px solid rgba(0,0,0,.06);border-radius:14px;background:#fff;
  text-decoration:none;color:inherit;transition:transform .15s,box-shadow .15s;
  box-shadow:0 1px 2px rgba(0,0,0,.03)
}
.card:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,.06)}
.ci{font-size:22px;flex-shrink:0}
.ct{font-size:.95rem;font-weight:700;margin-bottom:3px}
.cd{font-size:.78rem;opacity:.48;line-height:1.5}
.ca{
  width:14px;height:14px;fill:none;stroke:currentColor;stroke-width:2;
  margin-left:auto;opacity:.12;flex-shrink:0;transition:opacity .15s
}
.card:hover .ca{opacity:.4}
.ft{margin-top:22px;text-align:center;font-size:.72rem;opacity:.28;font-weight:500}
.ft a{color:inherit}
</style>
</head>
<body>
<div class="w">
  <h1>推荐曝光结构外部性研究导图</h1>
  <p class="sub">分别进入文献综述图谱与研究思考图谱。保持更轻的首页结构，避免卡片重叠和过度装饰。</p>
  <div class="cards">
    $CARDS$
  </div>
  <p class="ft">基于 <a href="https://markmap.js.org/">Markmap</a> · <a href="https://github.com/2711944586/mindmap">GitHub</a></p>
</div>
</body>
</html>"""


def build_page(stem: str, meta: dict[str, str]) -> str:
    source = ROOT / f"{stem}.mm.md"
    if not source.exists():
        return ""
    html_text = PAGE_TEMPLATE
    html_text = html_text.replace("$MD$", json.dumps(source.read_text("utf-8"), ensure_ascii=False))
    html_text = html_text.replace("$TITLE$", meta["title"])
    html_text = html_text.replace("$ACCENT$", meta["accent"])
    return html_text


def build_index() -> str:
    cards = []
    for stem, meta in PAGES.items():
        cards.append(
            f'<a class="card" href="{stem}.html">\n'
            f'  <span class="ci">{meta["icon"]}</span>\n'
            f'  <div><div class="ct">{meta["title"]}</div><div class="cd">{meta["sub"]}</div></div>\n'
            f'  <svg class="ca" viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>\n'
            f'</a>'
        )
    return INDEX_TEMPLATE.replace("$CARDS$", "\n".join(cards))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    for stem, meta in PAGES.items():
        html_text = build_page(stem, meta)
        if html_text:
            output = ROOT / f"{stem}.html"
            output.write_text(html_text, "utf-8")
            source_size = (ROOT / f"{stem}.mm.md").stat().st_size
            print(f"[OK] {output.name} ({source_size:,}→{output.stat().st_size:,})")

    index_path = ROOT / "index.html"
    index_path.write_text(build_index(), "utf-8")
    print("[OK] index.html")

    if args.serve:
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
        with http.server.HTTPServer(("", args.port), handler) as server:
            print(f"\n  http://localhost:{args.port}\n")
            server.serve_forever()


if __name__ == "__main__":
    main()
