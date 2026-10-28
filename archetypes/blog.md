---
title: '{{ replace .File.ContentBaseName "-" " " | title }}'
slug: '{{ .File.ContentBaseName }}'
date: '{{ time.Now.Format "2006-01-02" }}'
draft: true
description: ""
categories: []
tags: []
---

<!-- slug is load-bearing: [permalinks] blog = "/blog/:slug/" falls back to the
     title when it is absent, so a later title edit would change the published URL. -->

<!-- 新增、重新生成或替换配图的交付尺寸必须为 900 × 383px（精确比例 900:383，约 2.35:1），交付前核对实际像素。
     技术图优先保留可编辑矢量源；文字过密时拆图或重排，不拉伸、不裁切、不把高图压小塞入宽框。
     原尺寸例外仅限 scripts/legacy-image-sources.json 已固定的 39 张原字节不变历史图；
     不得自动追加清单，替换历史图也须遵守新尺寸。浏览器检查校验新图尺寸或历史图固定哈希。
     正文与封面默认按原比例全栏显示，列表才使用统一宽幅框。
     技术图提供原图入口，例如：[![流程与字段说明](images/01-flow.png)](images/01-flow.png)
     原图入口仅补充放大阅读，不能代替正文可读性；已有图片链接不要重复包裹。
     封面可直接使用 ![文章封面](images/00-cover.png)。 -->
