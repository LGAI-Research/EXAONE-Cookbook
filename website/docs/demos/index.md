---
layout: page
pageClass: ex-sub
title: Proof Gallery — EXAONE in other frameworks
description: Five external OSS agent harnesses — smolagents, browser-use, CrewAI, NanoClaw and Hermes Agent — running end to end on EXAONE.
---

<PageHeader
  eyebrow="Proof Gallery"
  title="EXAONE inside other frameworks"
  lede="EXAONE speaks the OpenAI-compatible protocol, so existing agent harnesses need an adapter rather than a rewrite. Each demo below is verified end to end against a pinned upstream version."
/>

<div class="ex-wrap ex-body">
<DemoGrid detailed />

<div class="vp-doc ex-note">

::: warning Upstream repositories are not vendored
The cookbook ships only the glue code in `implementations/`. Clone each upstream project into `submodules/` yourself — see [`implementations/README.md`](https://github.com/LGAI-Research/EXAONE-Cookbook/blob/main/implementations/README.md) § Upstream clone.

```bash
cp implementations/smolagents/.env.example implementations/smolagents/.env
uv sync --project implementations/smolagents
./implementations/uv_run.sh smolagents python scripts/check_env.py
```

:::

</div>
</div>
