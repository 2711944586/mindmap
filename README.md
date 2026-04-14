# mindmap

交互式 Markmap 思维导图，包含文献综述图谱和研究路线图谱。

## 在线地址

- 导航页: `https://2711944586.github.io/mindmap/`
- 文献综述导图: `https://2711944586.github.io/mindmap/literature_review.html`
- 研究路线导图: `https://2711944586.github.io/mindmap/research_journey.html`

## 文件

- `literature_review.mm.md`: 文献综述导图源文件
- `research_journey.mm.md`: 研究路线导图源文件
- `render_markmap.py`: 渲染脚本
- `index.html`: 导航页

## 本地更新

```powershell
python render_markmap.py
```

需要本地预览时：

```powershell
python render_markmap.py --serve
```

默认地址: `http://localhost:8080/`

## 静态部署

工作流文件: `.github/workflows/deploy-mindmap.yml`

```powershell
python render_markmap.py
git add .
git commit -m "Update mindmap"
git push origin main
```

推送后：

1. 打开 `https://github.com/2711944586/mindmap/actions`
2. 等待部署工作流完成
3. 打开上面的 Pages 地址

## 当前内容

1. `literature_review.html` 用于综述图谱展示。
2. `research_journey.html` 用于论文研究路线、对象层、方法链和评估边界展示。
3. 页面支持搜索、主题切换、展开全部和恢复初始状态。
