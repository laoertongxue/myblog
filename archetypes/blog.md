---
title: '{{ replace .File.ContentBaseName "-" " " | title }}'
slug: '{{ .File.ContentBaseName }}'
date: '{{ time.Now.Format "2006-01-02" }}'
draft: true
description: ""
summary: ""
categories: []
tags: []
---

<!-- slug is load-bearing: [permalinks] blog = "/blog/:slug/" falls back to the
     title when it is absent, so a later title edit would change the published URL. -->

<!-- 每篇文章只设计一张 900 × 383px 封面（精确比例 900:383，约 2.35:1），导出后核对实际像素。
     封面按适用图片技能制作，原生图形优先 SVG 排版；不裁切、拉伸旧图或用留白补边。
     可编辑源放在文章 bundle 外。
     front matter 显式配置 images: ["images/00-cover.png"]，正文首图也使用同一封面：
     ![文章封面](images/00-cover.png)
     其他正文配图保留自己的原始尺寸与比例，不套封面尺寸要求，也没有历史尺寸白名单。
     技术图可链接原图：[![流程与字段说明](images/01-flow.png)](images/01-flow.png)
     原图入口仅补充放大阅读，不能代替正文可读性；已有图片链接不要重复包裹。
     列表只展示这一张封面；上下篇始终为上一篇左、下一篇右两列，缺项留空。 -->

<!-- description 保持简短，用于 SEO、文章导语、搜索与订阅描述。
     summary 为可选的手写列表摘要，通常约 120–180 字，概括业务问题、案例或方法与阅读收益，不凑字数。
     列表优先使用 summary，空值回退 description；不使用自动生成的 Hugo .Summary，不强制长度或行数。 -->
