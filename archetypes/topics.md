---
title: '{{ replace .File.ContentBaseName "-" " " | title }}'
date: '{{ time.Now.Format "2006-01-02" }}'
draft: true
description: ""
summary: ""
weight: 0
---

<!-- Create as content/topics/<topic>/NN-name/index.md. Chapter order and the
     prev/next pager both come from `weight` (see layouts/_partials/lab/
     chapters.html); date is required, otherwise the Article schema would
     publish a 0001-01-01 datePublished. -->

<!-- description 保持简短，用于 SEO、文章导语、搜索与订阅描述。
     summary 为可选的手写列表摘要，通常约 120–180 字，概括业务问题、案例或方法与阅读收益，不凑字数。
     列表优先使用 summary，空值回退 description；不使用自动生成的 Hugo .Summary，不强制长度或行数。 -->
