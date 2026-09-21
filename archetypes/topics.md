---
title: '{{ replace .File.ContentBaseName "-" " " | title }}'
date: '{{ .Date.Format "2006-01-02" }}'
draft: true
description: ""
weight: 0
---

<!-- Create as content/topics/<topic>/NN-name/index.md. Chapter order and the
     prev/next pager both come from `weight` (see layouts/_partials/lab/
     chapters.html); date is required, otherwise the Article schema would
     publish a 0001-01-01 datePublished. -->
