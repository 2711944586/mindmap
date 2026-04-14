# 05_思维导图

交互式 Markmap 思维导图，涵盖文献综述图谱与最新版论文研究图谱。

**在线预览**: [https://2711944586.github.io/mindmap/](https://2711944586.github.io/mindmap/)

## 文件说明

| 文件 | 用途 |
| --- | --- |
| `literature_review.mm.md` | 文献综述图谱源文件 — 76 篇文献按六条研究线索组织 |
| `research_journey.mm.md` | 研究图谱源文件 — 对象层、三组件框架、理论边界与评估协议 |
| `render_markmap.py` | 渲染脚本 — 从 `.mm.md` 生成 HTML（纯 Python，无第三方依赖） |
| `index.html` | 着陆页 — 导航到两个思维导图 |
| `literature_review.html` | 文献综述图谱（可直接浏览器打开） |
| `research_journey.html` | 研究思考图谱（可直接浏览器打开） |

## 功能特性

- 🔍 **节点搜索** — 顶栏输入关键词实时高亮
- 📂 **展开与恢复初始** — 支持一键展开全部，并恢复到最初折叠状态
- 🌗 **Paper / Nocturne 主题** — 主题切换时同步切换配色与导图字体
- 📊 **节点/层深统计** — 左下角实时显示
- 🖨️ **打印优化** — 自动隐藏控件
- 📱 **响应式布局** — 顶部控制栏在窄屏下自动收束，避免首页与工具栏重叠

## 更新命令

```bash
python render_markmap.py          # 生成全部 HTML
python render_markmap.py --serve  # 生成并启动本地预览 (http://localhost:8080)
```

## 部署

通过 GitHub Actions 自动部署到 GitHub Pages，推送到 `main` 分支即触发。

## 当前内容

1. `literature_review` 保持参考文献导图主线。
2. `research_journey` 已同步最新论文原稿，围绕对象层、机制层、评估层更新研究图谱。
3. 目录本身就是部署根目录，可直接初始化并推送到 `2711944586/mindmap`。
