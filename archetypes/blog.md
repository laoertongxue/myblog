---
title: '{{ replace .File.ContentBaseName "-" " " | title }}'
slug: '{{ .File.ContentBaseName }}'
date: '{{ .Date.Format "2006-01-02" }}'
draft: true
description: ""
categories: []
tags: []
---

<!-- slug is load-bearing: [permalinks] blog = "/blog/:slug/" falls back to the
     title when it is absent, so a later title edit would change the published URL. -->
