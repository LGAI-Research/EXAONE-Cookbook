---
layout: page
pageClass: ex-sub
title: Proof Gallery — 다른 프레임워크 속 EXAONE
description: smolagents · browser-use · CrewAI · NanoClaw · Hermes Agent 등 5개 외부 OSS 하니스를 EXAONE으로 E2E 검증한 데모.
---

<PageHeader
  eyebrow="Proof Gallery"
  title="다른 프레임워크 안의 EXAONE"
  lede="EXAONE은 OpenAI 호환 프로토콜을 사용하므로 기존 에이전트 하니스는 재작성이 아니라 어댑터만으로 붙습니다. 아래 데모는 모두 고정된 upstream 버전에서 E2E로 검증되었습니다."
/>

<div class="ex-wrap ex-body">
<DemoGrid detailed />

<div class="vp-doc ex-note">

::: warning upstream 저장소는 포함되어 있지 않습니다
Cookbook은 `implementations/`의 접착 코드만 제공합니다. 각 upstream 프로젝트는 `submodules/`에 직접 clone 하세요 — [`implementations/README.md`](https://github.com/LGAI-Research/EXAONE-Cookbook/blob/main/implementations/README.md) § Upstream clone.

```bash
cp implementations/smolagents/.env.example implementations/smolagents/.env
uv sync --project implementations/smolagents
./implementations/uv_run.sh smolagents python scripts/check_env.py
```

:::

</div>
</div>
