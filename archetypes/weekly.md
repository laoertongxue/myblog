---
title: 'Weekly #{{ .File.ContentBaseName }} — '
date: '{{ time.Now.Format "2006-01-02" }}'
draft: true
description: ""
summary: ""
categories: ["周刊"]
tags: []
---

<!-- Create as content/weekly/NNN/index.md: [permalinks] uses :filename, so the
     directory number is both the URL (/weekly/NNN/) and the "Vol. NNN" label
     rendered by layouts/_partials/lab/row.html and article.html. -->

<!-- description 保持简短，用于 SEO、文章导语、搜索与订阅描述。
     summary 为可选的手写列表摘要，通常约 120–180 字，概括业务问题、案例或方法与阅读收益，不凑字数。
     列表优先使用 summary，空值回退 description；不使用自动生成的 Hugo .Summary，不强制长度或行数。 -->
