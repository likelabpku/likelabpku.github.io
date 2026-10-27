# 中英文网站维护

英文页面位于网站根目录；中文页面位于 `zh/`。两版共用图片、样式、交互脚本和 BibTeX，并使用相同的 GA4 测量 ID。

更新英文页面及 `i18n/zh-CN.json` 中的中文文案后，在仓库根目录运行：

```sh
python3 scripts/build_locales.py
```

脚本使用 Python 标准库，更新语言切换链接、语言标记、搜索别名和资源缓存版本，并生成五个中文页面。重复运行结果一致。直接修改 `zh/` 下的文件会在下次生成时被覆盖。英文正文是生成来源；增加新文案时请同步补充译文。

用户于 2026-10-27 确定：论文标题、摘要与作者署名保留英文原文；其余介绍、动态、研究成果说明及交互控件使用中文。论文标题在首页代表成果和动态中的引用也保留原文。

News 大标题中指代论文的部分，按对应英文大标题的原有措辞保留，包括简称或英文描述；只翻译发表、录用、报告等周围表述。例如 `GroundingME at CVPR 2026` 对应 `GroundingME 发表于 CVPR 2026`，`Dataset evaluation study in Natural Language Processing` 对应 `Dataset evaluation study 发表于 Natural Language Processing`。英文大标题采用简称时，中文版也采用该简称，不扩写为论文全名。展开列表中的正式论文标题继续保留英文原文。多篇论文汇总与获奖动态使用中文标题。

中文姓名依据现有个人照说明与校友核验资料；管龙宇（Longyu Guan）、宋佳霖（Jialin Song）、唐子超（Zichao Tang）由用户于 2026-10-27 确认。两版论文搜索均支持已核对成员的中英文姓名。

导航中的“中文 / EN”按钮切换到对应页面；启用 JavaScript 时同时保留查询参数、锚点和论文搜索、年份、类型条件。中文页的站内导航保持中文，图片和下载文件从上一级目录读取。

预览两种语言可运行 `python3 -m http.server 8765 --bind 127.0.0.1`，访问 `/index.html` 和 `/zh/index.html`。关闭 JavaScript 时两版正文及语言切换链接仍可使用。
